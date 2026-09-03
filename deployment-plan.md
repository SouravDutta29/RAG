# Streamlit Monolithic Deployment Plan

This document outlines the deployment strategy for the **Groww FAQ Assistant**. Since the architecture has been successfully refactored into a monolithic design, **both the frontend and backend** will be deployed together natively on **Streamlit Community Cloud**.

---

## 1. Architecture Overview

- **Host:** Streamlit Community Cloud (Free Tier)
- **Deployment Model:** Monolithic (Streamlit handles UI + Backend Logic)
- **Database:** Local embedded ChromaDB (persisted in the repo via `.github/workflows/schedule.yml`)
- **LLM/Embeddings:** Groq API (Llama-3) & HuggingFace Models loaded into RAM at runtime via `@st.cache_resource`.

## 2. Pre-Deployment Requirements

Ensure the following files are present in your GitHub repository root/subdirectories:
- `hdfc-rag-chatbot/ui/app.py` (Main entry point)
- `hdfc-rag-chatbot/requirements.txt` (Python dependencies)
- `.github/workflows/schedule.yml` (For daily data updates)

> **Important Memory Warning:** 
> Streamlit Community Cloud provides **1 GB of RAM** on the free tier. When the app boots, it loads ChromaDB and the HuggingFace BGE Reranker into memory. If the app crashes with an **Out Of Memory (OOM)** error upon deployment, you will need to replace the BGE Reranker (`BAAI/bge-reranker-base`) with a smaller model or rely entirely on ChromaDB's BM25 search.

## 3. Deployment Steps

Follow these precise steps to host your application online for free:

### Step 1: Upload to GitHub
Streamlit Cloud deploys directly from your GitHub repository.
1. Create a new public repository on [GitHub](https://github.com/).
2. Push your local `RAG` directory to the repository:
   ```bash
   git add .
   git commit -m "Ready for Streamlit Deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

### Step 2: Set up GitHub Actions (Automated Scraping)
To ensure the backend data stays up-to-date:
1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Add a new repository secret named `GROQ_API_KEY` and paste your actual API key.
3. Go to **Settings** -> **Actions** -> **General** -> Check **Read and write permissions** under Workflow permissions.

### Step 3: Deploy on Streamlit Community Cloud
1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/) using your GitHub account.
2. Click **New app** -> **Use existing repo**.
3. Configure the deployment settings:
   - **Repository:** `YOUR_USERNAME/YOUR_REPO_NAME`
   - **Branch:** `main`
   - **Main file path:** `hdfc-rag-chatbot/ui/app.py`
4. **Configure Secrets (Critical):**
   - Click **Advanced settings**.
   - In the secrets text box, add your Groq API key:
     ```toml
     GROQ_API_KEY="your-groq-api-key-here"
     ```
5. Click **Deploy!**

## 4. Post-Deployment Verification

Once deployed, Streamlit will provide you with a public URL (e.g., `https://your-app-name.streamlit.app`).

**Verification Checklist:**
- [ ] **Initial Boot:** Open the URL. The first load will take ~30-60 seconds as the backend AI models are downloaded and cached.
- [ ] **Test Query:** Ask "What is the expense ratio of HDFC Small Cap?" to verify the LLM and database are successfully connected.
- [ ] **Data Refresh Check:** Wait 24 hours to ensure the GitHub Action automatically updates the database and restarts the Streamlit server with fresh data.
