# 🏗️ BIS Standard Discovery Engine
**Team Name:** Sigma Squad (IIT Tirupati)  
**Hackathon:** BIS x Sigma Squad AI Hackathon 2026

## 🚀 Overview
An AI-powered Retrieval-Augmented Generation (RAG) pipeline designed to identify relevant Indian Standards (IS) from the SP 21 Building Materials handbook. The system utilizes metadata-aware filtering and LLM-based re-ranking to achieve high precision and low latency.

## 📊 Performance Metrics
Based on evaluation against the hackathon test suite:
- **Hit Rate @3:** 90.00%
- **MRR @5:** 0.85
- **Average Latency:** 3.48 seconds

## 🛠️ Tech Stack
- **LLM:** Llama-3.3-70b-versatile (via Groq)
- **Vector Database:** ChromaDB
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2`
- **Interface:** Streamlit

## 📂 Project Structure
- `inference.py`: Core RAG and re-ranking logic.
- `ingest.py`: PDF processing and context-aware vectorization.
- `app.py`: Streamlit dashboard for real-time querying.
- `vector_db/`: Persisted vector embeddings of BIS SP 21.
- `presentation.pdf`: 10-slide technical project deck.

## ⚙️ Setup & Usage
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
