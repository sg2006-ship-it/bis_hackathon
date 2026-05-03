import os
import re
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# --- Configuration ---
PDF_PATH = "data/SP21_Building_Materials.pdf"
DB_DIR = "./vector_db"

# 1. Global Index Map (Derived from Page 11)
# Format: {Section_Num: "Section Title"}
SECTION_MAP = {
    "1": "CEMENT AND CONCRETE",
    "2": "BUILDING LIMES",
    "3": "STONES",
    "4": "WOOD PRODUCTS FOR BUILDING",
    "5": "GYPSUM BUILDING MATERIALS",
    "6": "TIMBER",
    "7": "BITUMEN AND TAR PRODUCTS",
    "8": "FLOOR, WALL, ROOF COVERINGS AND FINISHES",
    "9": "WATER PROOFING AND DAMP PROOFING MATERIALS",
    "10": "SANITARY APPLIANCES AND WATER FITTINGS",
    "11": "BUILDER’S HARDWARE",
    "12": "WOOD PRODUCTS",
    "13": "DOORS, WINDOWS AND SHUTTERS",
    "14": "CONCRETE REINFORCEMENT",
    "15": "STRUCTURAL STEELS",
    "16": "LIGHT METAL AND THEIR ALLOYS",
    "17": "STRUCTURAL SHAPES",
    "18": "WELDING ELECTRODES AND WIRES",
    "19": "THREADED FASTENERS AND RIVETS",
    "20": "WIRE ROPES AND WIRE PRODUCTS",
    "21": "GLASS",
    "22": "FILLERS, STOPPERS AND PUTTIES",
    "23": "THERMAL INSULATION MATERIALS",
    "24": "PLASTICS",
    "25": "CONDUCTORS AND CABLES",
    "26": "WIRING ACCESSORIES",
    "27": "GENERAL"
}

# 2. Category Keywords to watch for (Dynamic state tracking)
CATEGORIES = ["AGGREGATES", "CEMENT", "CEMENT MATRIX PRODUCTS", "ASBESTOS CEMENT PRODUCTS", "CONCRETE PIPES", "JOINTS"]

def ingest_bis_data():
    print("📖 Loading PDF and initializing structural map...")
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()

    # Trackers for Context Inheritance
    current_section_id = "0"
    current_section_name = "General"
    current_category = "General"
    last_is_code = "General"

    final_documents = []
    
    # Semantic Splitter - prioritizing Indian Standard entries
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150,
        separators=["\nIS ", "\nSECTION", "\n\n", "\n", " "]
    )

    for i, page in enumerate(pages):
        content = page.page_content
        phys_page = i + 1
        
        # --- A. Update Section Context ---
        # Look for "SECTION X"
        section_match = re.search(r"SECTION\s+(\d+)", content, re.IGNORECASE)
        if section_match:
            current_section_id = section_match.group(1)
            current_section_name = SECTION_MAP.get(current_section_id, "Unknown")
            print(f"📍 Entering {current_section_name} (Physical Page {phys_page})")

        # --- B. Update Category Context ---
        for cat in CATEGORIES:
            if cat in content:
                current_category = cat

        # --- C. Extract IS Codes on this page ---
        is_codes_found = re.findall(r"IS\s?(\d+)\s?:\s?(\d{4})", content)
        if is_codes_found:
            last_is_code = f"IS {is_codes_found[0][0]}:{is_codes_found[0][1]}"

        # --- D. Chunk and Tag ---
        chunks = text_splitter.split_text(content)
        for chunk in chunks:
            # Check if this specific chunk contains a new IS code to override last_is_code
            chunk_is_match = re.search(r"IS\s?(\d+)\s?:\s?(\d{4})", chunk)
            local_is_code = f"IS {chunk_is_match.group(1)}:{chunk_is_match.group(2)}" if chunk_is_match else last_is_code
            
            metadata = {
                "section": current_section_name,
                "category": current_category,
                "is_code": local_is_code,
                "physical_page": phys_page,
                "internal_label": (re.search(r"(\d+\.\d+)", chunk).group(1) if re.search(r"(\d+\.\d+)", chunk) else "N/A")
            }
            
            final_documents.append(Document(page_content=chunk, metadata=metadata))

    # --- 3. Vector Storage ---
    print(f"🧠 Generating embeddings for {len(final_documents)} chunks...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'} # Switch to 'cuda' on Kali if GPU is available
    )

    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)

    vector_db = Chroma.from_documents(
        documents=final_documents,
        embedding=embeddings,
        persist_directory=DB_DIR,
        collection_name="bis_compliance"
    )
    
    print(f"✅ Success! Vector DB saved to {DB_DIR}")

if __name__ == "__main__":
    ingest_bis_data()
