import re
from langchain_community.document_loaders import PyPDFLoader

# Configuration based on your previous output
PDF_PATH = "data/SP21_Building_Materials.pdf"
INDEX_PAGE_PHYSICAL = 11  # The "Global Router"
SEC1_START_PHYSICAL = 13  # Where "SECTION 1" was found

# The "Map" derived from Page 11
GLOBAL_INDEX = {
    "1": {"title": "CEMENT AND CONCRETE", "internal_range": "1-81"},
    "2": {"title": "BUILDING LIMES", "internal_range": "1-15"},
    "10": {"title": "SANITARY APPLIANCES", "internal_range": "1-235"},
    # ... this will be fully populated in the final ingest.py
}

def demo_mapping_logic():
    print("--- 🔬 PHASE 1: LOADING GLOBAL INDEX ---")
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()
    
    # Verify we can read the Global Index (Page 11)
    index_text = pages[INDEX_PAGE_PHYSICAL - 1].page_content
    if "SECTION 1" in index_text:
        print(f"✅ Successfully read Global Index on Page {INDEX_PAGE_PHYSICAL}")

    print("\n--- 🔬 PHASE 2: TRACKING SECTION 1 ---")
    
    current_category = "PRE-INDEX"
    
    # We scan a range to see if we can catch the transition from Index to Data
    # Looking at Pages 14 to 25 (where you found the bulk of IS codes)
    for i in range(SEC1_START_PHYSICAL, SEC1_START_PHYSICAL + 12):
        content = pages[i].page_content
        phys_page = i + 1
        
        # 1. Extract the Internal Label (e.g., 1.5)
        internal_label = "Unknown"
        label_match = re.search(r"(\d+\.\d+)", content)
        if label_match:
            internal_label = label_match.group(1)

        # 2. Category Detection Logic
        # In Section 1, headers like 'AGGREGATES' or 'CEMENT' appear in ALL CAPS
        # We look for specific headers we know exist in your contents table
        for cat in ["AGGREGATES", "CEMENT", "ASBESTOS CEMENT PRODUCTS"]:
            if cat in content:
                current_category = cat

        # 3. IS Code Extraction
        is_codes = re.findall(r"IS\s?(\d+)\s?:\s?(\d{4})", content)
        
        # 4. Simulation of Metadata Assignment
        print(f"Page {phys_page} [Internal {internal_label}]:")
        print(f"  ├─ Section: {GLOBAL_INDEX['1']['title']}")
        print(f"  ├─ Active Category: {current_category}")
        
        if is_codes:
            # We only show the first 2 codes to keep the terminal clean
            print(f"  └─ Sample Codes: {is_codes[:2]}")
        else:
            print(f"  └─ (No new IS codes - inheriting from previous page context)")
        print("-" * 30)

if __name__ == "__main__":
    demo_mapping_logic()
