# Evaluation Strategy & Metrics: HDFC Mutual Funds RAG Chatbot

This document defines the evaluation protocol, metrics, and testing criteria for each phase of the project as outlined in [ImplementationPlan.md](file:///c:/Users/Windows/Desktop/RAG/ImplementationPlan.md).

---

## Phase 1: Environment & Web Scraping Layer

**Objective:** Ensure the web crawler extracts data accurately from the 5 Groww URLs without missing mandatory financial figures.

| Evaluation Metric | Target | Testing Method |
| :--- | :--- | :--- |
| **Extraction Success Rate** | $100\%$ | Run `pytest tests/test_scraper.py`. Assert that 5 output JSON files are created. |
| **Schema Compliance** | $100\%$ | Pass all 5 JSON payloads through Pydantic `FundScheme` validation. Zero validation errors allowed. |
| **Critical Field Completeness** | $100\%$ | Check that `NAV`, `AUM`, `Expense Ratio`, and `Returns` are NOT `null`, `NaN`, or empty strings. |
| **Scraping Duration** | $< 30 \text{ sec}$ | Measure end-to-end time for Playwright to navigate, parse, and save all 5 pages. |

---

## Phase 2: Indexing & Dual Vector Pipeline

**Objective:** Validate that the raw JSON is properly chunked, embedded via the BGE model, and successfully ingested into both ChromaDB and the BM25 index.

| Evaluation Metric | Target | Testing Method |
| :--- | :--- | :--- |
| **Chunk Constraint Check** | $100\%$ | Script asserts no chunk exceeds $512$ tokens (using `tiktoken` or model-specific tokenizer). |
| **Corpus Completeness** | $25 \text{ chunks}$ | Query `chromadb.collection.count()`. Must equal exactly 25 chunks (5 funds × 5 sections). |
| **Embedding Dimension** | $384$ | Assert that returned embeddings from BGE-small-en-v1.5 match the 384-dim shape constraint. |
| **BM25 Lexical Integrity** | Pass | Run `test_bm25.py` to assert index serialization (`.pkl`) is successfully loaded into memory and matches chunk array length. |

---

## Phase 3: Hybrid Retrieval & Reranking Engine

**Objective:** Ensure the routing logic correctly fires and the retrieval pipeline (RRF + Cross-Encoder) surfaces the most relevant chunks in the Top-5.

| Evaluation Metric | Target | Testing Method |
| :--- | :--- | :--- |
| **Router Accuracy** | $100\%$ | Feed a set of 20 test queries. Assert the router correctly assigns `DIRECT_LOOKUP`, `COMPARATIVE`, `PORTFOLIO_HOLDING`, or `GUIDANCE`. |
| **Hit Rate @ 5** | $> 95\%$ | For a test set of 20 factual queries, assert that the chunk containing the answer is present within the Top 5 returned by the reranker. |
| **Mean Reciprocal Rank (MRR)** | $> 0.85$ | Calculate MRR of the target chunk across the 20 test queries. Higher rank = better Cross-Encoder performance. |
| **Out-of-Bounds Rejection** | $100\%$ | Feed queries about "SBI Mutual Fund" or "Axis Bluechip". Assert retrieval returns a low-confidence score, triggering fallback. |

---

## Phase 4: LLM Generation & Financial Guardrails

**Objective:** Validate the prompt construction, Groq LLM streaming behavior, and most importantly, the Numeric Fact Verifier.

| Evaluation Metric | Target | Testing Method |
| :--- | :--- | :--- |
| **Numeric Fact Accuracy** | $100\%$ | Run the Verifier over 50 LLM-generated responses. Assert it catches 100% of injected hallucinations (e.g., swapping NAV values). |
| **Disclaimer Inclusion** | $100\%$ | Regex check on all generated outputs to guarantee the "Not financial advice" text is appended. |
| **Source Citation Match** | $100\%$ | Assert the generated markdown contains `https://groww.in/mutual-funds/...` URL matching the fund mentioned in the answer. |
| **Groq Inference Latency (TTFT)** | $< 500 \text{ ms}$ | Measure Time-To-First-Token (TTFT) from the Groq API (Llama 3 8B) for 10 sequential queries. |

---

## Phase 5: API Backend & Chat UI

**Objective:** Verify that the FastAPI backend routes handle traffic correctly, cache logic works, and the UI correctly parses markdown/SSE.

| Evaluation Metric | Target | Testing Method |
| :--- | :--- | :--- |
| **Endpoint Health / Uptime** | $200 \text{ OK}$ | Send GET/POST requests to `/health`, `/chat`, `/funds`, `/compare` via `pytest-asyncio`. |
| **Cache Hit Latency** | $< 50 \text{ ms}$ | Send duplicate queries. Assert the second query returns from Redis instead of hitting Groq/Chroma. |
| **Concurrent Load Test** | $50 \text{ RPS}$ | Run `Locust` or `k6` load test hitting the `/chat` endpoint with cached requests without dropping connections. |
| **SSE Streaming Integrity** | Pass | Run simulated client. Assert full markdown stream finishes with `[DONE]` signal and valid JSON chunks. |

---

## Phase 6: System Evaluation & Quality Assurance (Ragas)

**Objective:** Run the end-to-end evaluation pipeline on the Golden Test Set (50 Queries) using `Ragas` to score the RAG system mathematically.

| Ragas Metric | Minimum Target | Description |
| :--- | :--- | :--- |
| **Faithfulness** | $\ge 0.95$ | Uses LLM-as-a-judge to verify that every claim in the generated answer can be logically deduced from the retrieved chunks. |
| **Answer Relevance** | $\ge 0.90$ | Measures how well the generated answer addresses the original query (penalizes incomplete or overly verbose answers). |
| **Context Precision** | $\ge 0.85$ | Measures whether the most relevant chunks are ranked at the very top of the retrieved context. |
| **Numeric Accuracy** | $1.00$ | Strict custom metric: Verifies every parsed number ($, %, \text{dates}$) in the answer perfectly matches the exact string in the source JSON. |
