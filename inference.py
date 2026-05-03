import json
import argparse
import time
import os
import re
from groq import Groq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- Setup ---
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(
    persist_directory="./vector_db", 
    embedding_function=embeddings,
    collection_name="bis_compliance"
)

CATEGORIES = ["AGGREGATES", "CEMENT", "CEMENT MATRIX PRODUCTS", "ASBESTOS CEMENT PRODUCTS", "CONCRETE PIPES", "JOINTS"]

def get_answer(query_text):
    # 1. Broad Retrieval (k=20) to ensure the needle is in the haystack
    # We use a lower k if a specific category is detected to maintain precision
    active_category = next((cat for cat in CATEGORIES if cat.lower() in query_text.lower()), None)
    
    search_kwargs = {"k": 20}
    if active_category:
        search_kwargs["filter"] = {"category": active_category}
    
    docs = vector_db.similarity_search(query_text, **search_kwargs)
    
    # 2. Extract and Deduplicate with Metadata Priority
    unique_candidates = {}
    for d in docs:
        code = d.metadata.get('is_code', 'General')
        if code == "General": continue
        
        if code not in unique_candidates:
            unique_candidates[code] = {
                "text": d.page_content[:500],
                "section": d.metadata.get('section', 'N/A')
            }

    if not unique_candidates:
        return []

    # 3. Two-Stage Reasoning (The MRR Booster)
    # We ask the LLM to 'score' them internally to ensure the best match is #1
    context_str = "\n".join([f"- {c} (Section: {m['section']}): {m['text']}" for c, m in unique_candidates.items()])
    
    prompt = f"""
    QUERY: {query_text}
    
    AVAILABLE STANDARDS:
    {context_str}

    TASK: 
    1. Analyze the QUERY and the AVAILABLE STANDARDS.
    2. Rank the top 5 IS codes that directly govern the product mentioned.
    3. Ensure the most specific standard is listed FIRST (Crucial for MRR).
    
    OUTPUT: A comma-separated list of IS codes only (e.g., IS 456: 2000, IS 269: 2015).
    """

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a BIS Technical Expert. Output ONLY the ranked IS codes."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=200
        )
        content = response.choices[0].message.content.strip()
        found = re.findall(r"IS\s?\d+(?:\s?\(Part\s?\d+\))?[:\s]+\d{4}", content)
        
        # Unique list preserving the LLM's ranked order
        final_list = []
        for c in found:
            c_clean = c.strip()
            if c_clean not in final_list:
                final_list.append(c_clean)
        
        return final_list[:5]
    except:
        return list(unique_candidates.keys())[:5]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        input_data = json.load(f)

    results = []
    for item in input_data:
        start_time = time.time()
        answer = get_answer(item.get('query', ''))
        
        res = {
            "id": item["id"],
            "retrieved_standards": answer,
            "latency_seconds": round(time.time() - start_time, 4)
        }
        if args.local and "expected_standards" in item:
            res["expected_standards"] = item["expected_standards"]
        results.append(res)
        time.sleep(0.1) # Safe throttle

    with open(args.output, "w") as f:
        json.dump(results, f, indent=4)
    print(f"✅ Submission Ready. Latency should remain under 1s. Accuracy target: 85%+")

if __name__ == "__main__":
    main()
