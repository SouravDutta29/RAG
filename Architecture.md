# System Architecture: Financial RAG Chatbot for HDFC Mutual Funds

## 1. Executive System Overview

The **HDFC Mutual Funds RAG Chatbot** is a production-grade Retrieval-Augmented Generation (RAG) system engineered to deliver accurate, context-grounded, and hallucination-free answers to user queries about five specific HDFC mutual fund schemes hosted on Groww.

**Knowledge Corpus:** Strictly limited to 5 specific Groww mutual fund web pages for HDFC schemes (Mid-Cap, Small-Cap, Multi-Cap, Large-Cap, Gold FoF). **No PDFs, CSV files, APIs, databases, or any other external document sources are used.**

**External Data Sources — Exclusively the following 5 Groww URLs:**

| # | Fund Scheme | Groww URL |
| :--- | :--- | :--- |
| 1 | HDFC Mid Cap Fund Direct Growth | `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth` |
| 2 | HDFC Small Cap Fund Direct Growth | `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth` |
| 3 | HDFC Gold ETF Fund of Fund Direct Plan Growth | `https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth` |
| 4 | HDFC Multi Cap Fund Direct Growth | `https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth` |
| 5 | HDFC Large Cap Fund Direct Growth | `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth` |

**Core Design Principles:**
- **Bounded Corpus:** All answers are strictly grounded in the above 5 Groww pages only — no external LLM knowledge, no PDFs, no third-party APIs, and no other document sources.
- **Hybrid Retrieval:** Dense vector search + sparse BM25 keyword search fused via Reciprocal Rank Fusion (RRF) to handle both semantic and exact-match financial queries.
- **Financial Guardrails:** Post-generation verification that every numeric metric (NAV, AUM, Expense Ratio) exists verbatim in retrieved context.

---

## 2. High-Level End-to-End System Architecture

```mermaid
flowchart TB
    subgraph Sources["📄 Data Sources (Groww)"]
        URL1["HDFC Mid Cap Fund\ngroww.in/mutual-funds/hdfc-mid-cap..."]
        URL2["HDFC Small Cap Fund\ngroww.in/mutual-funds/hdfc-small-cap..."]
        URL3["HDFC Gold ETF FoF\ngroww.in/mutual-funds/hdfc-gold-etf..."]
        URL4["HDFC Multi Cap Fund\ngroww.in/mutual-funds/hdfc-multi-cap..."]
        URL5["HDFC Large Cap Fund\ngroww.in/mutual-funds/hdfc-large-cap..."]
    end

    subgraph Ingestion["⚙️ Layer 1: Data Ingestion & ETL"]
        Scraper["Web Crawler\n(Playwright)"]
        Parser["DOM + JSON Parser"]
        Normalizer["Schema Normalizer\n(Structured JSON/MD)"]
    end

    subgraph Indexing["🗂️ Layer 2: Dual Index Pipeline"]
        Chunker["Semantic Section Chunker\n(Chunk=512, Overlap=64)"]
        Embedder["Embedding Model\n(bge-small-en-v1.5)"]
        VectorDB[("🔵 Vector Store\nChromaDB / Qdrant\nHNSW Index")]
        BM25DB[("🟡 BM25 Index\nInverted Lexical Index")]
    end

    subgraph Retrieval["🔍 Layer 3: Hybrid Retrieval & Reranking"]
        Router["Query Intent Router"]
        Dense["Dense Vector Search\nTop-K=10"]
        Sparse["BM25 Keyword Search\nTop-K=10"]
        RRF["Intent-Weighted RRF Fusion\n(k=60)"]
        Reranker["Cross-Encoder Reranker\n(bge-reranker-base)\nTop-5 Final Chunks"]
    end

    subgraph Generation["🤖 Layer 4: LLM + Guardrails"]
        Prompt["Financial Prompt Builder\n(System + Context + Rules)"]
        LLM["LLM Engine\n(Groq API - Llama 3)"]
        Verifier["Fact & Citation Verifier\n+ Disclaimer Appender"]
    end

    subgraph Serving["🌐 Layer 5: API & User Interface"]
        API["FastAPI REST Backend\n/chat  /ingest  /funds"]
        UI["Web Chat Interface\n(Streamlit / Next.js)"]
    end

    Sources --> Scraper
    Scraper --> Parser --> Normalizer
    Normalizer --> Chunker
    Chunker --> Embedder --> VectorDB
    Chunker --> BM25DB

    UI -->|User Query| API
    API --> Router
    Router --> Dense --> VectorDB
    Router --> Sparse --> BM25DB
    VectorDB --> RRF
    BM25DB --> RRF
    RRF --> Reranker
    Reranker --> Prompt
    Prompt --> LLM --> Verifier
    Verifier --> API --> UI
```

---

## 3. Layer-by-Layer Data Flow Diagrams

### 3.1 Layer 1 — Data Ingestion & ETL Data Flow

```mermaid
flowchart LR
    subgraph Input
        G1["groww.in/..hdfc-mid-cap.."]
        G2["groww.in/..hdfc-small-cap.."]
        G3["groww.in/..hdfc-gold-etf.."]
        G4["groww.in/..hdfc-multi-cap.."]
        G5["groww.in/..hdfc-large-cap.."]
    end

    subgraph Extraction
        PW["Playwright Browser\nHeadless Chromium\n(renders dynamic JS)"]
        JSON_EX["__NEXT_DATA__ JSON\nExtractor\n(NAV, AUM, Returns)"]
        HTML_EX["HTML DOM Extractor\n(Holdings Table,\nSector Allocation,\nExit Load)"]
    end

    subgraph Normalization
        NORM["JSON Schema Normalizer"]
        VALID["Data Validator\n(Type checks, null guards)"]
        STORE["Raw Store\n(JSON files per scheme)"]
    end

    Input --> PW
    PW --> JSON_EX
    PW --> HTML_EX
    JSON_EX --> NORM
    HTML_EX --> NORM
    NORM --> VALID --> STORE
```

**Extracted Data Fields per Fund:**

| Field | Source Location in DOM | Example |
| :--- | :--- | :--- |
| `nav` | `__NEXT_DATA__.props.fundDetails.nav` | `235.87` |
| `nav_date` | Header NAV section | `18 Aug '26` |
| `aum_cr` | Fund details section | `1,05,142.69 Cr` |
| `expense_ratio` | Fund details section | `0.75%` |
| `min_sip` | Fund details section | `₹100` |
| `rating_stars` | Rating badge | `5` |
| `return_1y_pct` | Return calculator table | `+7.12%` |
| `return_3y_pct` | Return stats ticker | `+20.30%` |
| `risk_label` | Pill tags | `Very High Risk` |
| `top_holdings` | Holdings table rows | `{stock, weight%}` list |
| `sector_allocation` | Sector chart data | `{sector, weight%}` list |
| `exit_load_rule` | Scheme info section | `1% if redeemed < 1yr` |
| `benchmark_index` | Scheme info section | `NIFTY Midcap 150 TRI` |

---

### 3.2 Layer 2 — Indexing & Vector Store Data Flow

```mermaid
flowchart LR
    subgraph Input
        RAW["Normalized JSON\n(per fund scheme)"]
    end

    subgraph ChunkBuilder["Semantic Section Chunker"]
        S1["Section 1: Scheme Overview\n& Risk Profile"]
        S2["Section 2: Key Financial\nIndicators\n(NAV, AUM, Expense Ratio,\nMin SIP, Rating)"]
        S3["Section 3: Historical Returns\n(1D, 1Y, 3Y, 5Y)"]
        S4["Section 4: Portfolio\n(Top Holdings, Sector Weights)"]
        S5["Section 5: Scheme Rules\n(Exit Load, Benchmark, Fund Manager)"]
    end

    subgraph DualIndex["Dual Indexing"]
        EMB["Embedding Model\nbge-small-en-v1.5\n384-dim vectors"]
        VDB[("Vector DB\nChromaDB / Qdrant\n(HNSW Index)")]
        BM25["BM25 Builder\nInverted Index\n(TF-IDF term weights)"]
    end

    RAW --> S1 & S2 & S3 & S4 & S5
    S1 & S2 & S3 & S4 & S5 --> EMB --> VDB
    S1 & S2 & S3 & S4 & S5 --> BM25
```

**Chunk Metadata Schema (per vector record):**

```json
{
  "chunk_id": "hdfc_mid_cap_kfi_001",
  "scheme_slug": "hdfc-mid-cap-fund-direct-growth",
  "scheme_name": "HDFC Mid Cap Fund Direct Growth",
  "fund_house": "HDFC Mutual Fund",
  "category": "Equity - Mid Cap",
  "section": "Key Financial Indicators",
  "content": "HDFC Mid Cap Fund Direct Growth NAV as of 18 Aug 2026 is ₹235.87. Expense Ratio: 0.75%. AUM: ₹1,05,142.69 Cr. Minimum SIP: ₹100. Rating: 5 Stars.",
  "metadata": {
    "nav": 235.87,
    "aum_cr": 105142.69,
    "expense_ratio_pct": 0.75,
    "min_sip": 100,
    "rating": 5,
    "risk": "Very High",
    "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "scraped_at": "2026-08-19T00:12:00Z"
  }
}
```

---

### 3.3 Layer 3 — Hybrid Retrieval & Reranking Data Flow

```mermaid
flowchart TD
    Q["User Query\ne.g. 'Compare expense ratio:\nHDFC Mid Cap vs Small Cap'"]

    subgraph Router["Query Intent Router"]
        R1["Direct Lookup\n(NAV / Expense Ratio / AUM)"]
        R2["Comparative Query\n(Fund A vs Fund B)"]
        R3["Portfolio / Holding Query"]
        R4["Guidance / Explanation Query"]
    end

    subgraph Retrieval
        DENSE["Dense Vector Search\n(Cosine Similarity, Top-10)"]
        SPARSE["BM25 Keyword Search\n(Top-10)"]
    end

    subgraph Ranking
        RRF_MERGE["Intent-Weighted RRF Fusion\nScore = w_d/(60+rank_d) + w_s/(60+rank_s)"]
        RERANK["Cross-Encoder Reranker\nbge-reranker-base\nTop-5 Chunks Selected"]
    end

    Q --> Router
    Router --> DENSE & SPARSE
    DENSE --> RRF_MERGE
    SPARSE --> RRF_MERGE
    RRF_MERGE --> RERANK
    RERANK --> OUT["Top-5 Context Chunks\n→ Prompt Builder"]
```

**Query Routing Logic:**

| Query Type | Routing Strategy | Example Query |
| :--- | :--- | :--- |
| **Direct Lookup** | BM25-priority (Sparse=0.8, Dense=0.2) | *"What is the NAV of HDFC Small Cap Fund?"* |
| **Comparative** | Balanced (Sparse=0.5, Dense=0.5) | *"Compare AUM of HDFC Mid Cap vs Multi Cap"* |
| **Portfolio/Holdings** | Dense-priority (Sparse=0.2, Dense=0.8) | *"Does HDFC Large Cap Fund hold HDFC Bank?"* |
| **Guidance/Explanation** | Dense-priority (Sparse=0.2, Dense=0.8) | *"Explain the exit load of HDFC Gold FoF"* |

---

### 3.4 Layer 4 — LLM Generation & Guardrail Data Flow

```mermaid
flowchart LR
    CTX["Top-5 Retrieved Chunks\n+ Metadata"]
    QRY["Original User Query"]

    subgraph Prompt["Prompt Construction"]
        SYS["System Persona Block\n(Financial Expert Rules)"]
        RULES["Anti-Hallucination Rules\n(Must match context verbatim)"]
        CTXBLK["Retrieved Context Block\n(Formatted fund data)"]
        QBLK["User Query Block"]
    end

    subgraph LLM_GEN["LLM Generation"]
        MODEL["Groq API (Llama 3)\n(Streaming Token Output)"]
    end

    subgraph Guardrails["Output Guardrails"]
        NUM_CHK["Numeric Fact Verifier\n(Checks NAV, AUM, %s against context)"]
        CITE["Citation Injector\n(Appends source URLs)"]
        DISC["Disclaimer Appender\n('Not financial advice...')"]
    end

    CTX --> CTXBLK
    QRY --> QBLK
    SYS & RULES & CTXBLK & QBLK --> MODEL
    MODEL --> NUM_CHK --> CITE --> DISC --> RESP["Final Response\n→ API → UI"]
```

**Prompt Template:**

```
SYSTEM:
You are a certified financial data assistant specializing in HDFC Mutual Funds.
Answer ONLY using the retrieved context. Do not use any external knowledge.

RULES:
1. Every numeric value (NAV, Expense Ratio, AUM, SIP, Returns %) must be copied exactly from context.
2. If context is insufficient, respond: "Verified data not available in the knowledge base."
3. For comparative queries, present results in a markdown table.
4. Cite the Groww source URL for every fund referenced.
5. Always end with: ⚠️ Disclaimer: This is not financial advice. Past performance is not indicative of future returns.

CONTEXT:
{retrieved_chunks}

QUERY:
{user_query}

RESPONSE:
```

---

### 3.5 Layer 5 — API & User Interface Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Investor / User
    participant UI as Web Chat UI
    participant API as FastAPI Backend
    participant RAG as RAG Engine
    participant Cache as Response Cache

    User->>UI: Types query
    UI->>API: POST /api/v1/chat { query, history }
    API->>Cache: Check cached response (TTL=1hr)
    alt Cache Hit
        Cache-->>API: Return cached answer
    else Cache Miss
        API->>RAG: Execute Retrieval + Generation Pipeline
        RAG-->>API: Stream response tokens + citations
        API->>Cache: Store response in cache
    end
    API-->>UI: Stream tokens (SSE / WebSocket)
    UI-->>User: Render response with fund table + source links
```

**API Endpoints:**

| Endpoint | Method | Description | Response |
| :--- | :--- | :--- | :--- |
| `/api/v1/chat` | `POST` | Submit investor query; streams grounded answer | SSE token stream + citations |
| `/api/v1/ingest` | `POST` | Re-triggers scraper for all 5 Groww URLs; rebuilds index | Job status + timestamp |
| `/api/v1/funds` | `GET` | Lists all 5 supported HDFC fund schemes + live NAVs | JSON fund list |
| `/api/v1/compare` | `POST` | Structured side-by-side comparison of 2+ funds | Comparison table JSON |
| `/api/v1/health` | `GET` | System health check (Vector DB, Groq API connectivity) | Status JSON |

---

## 4. Technology Stack Comparison

| Layer | Component | Primary Choice | Alternative | Reason for Primary Choice |
| :--- | :--- | :--- | :--- | :--- |
| **Scraping** | Web Crawler | `Playwright` (Python) | `BeautifulSoup` + `requests` | Groww renders via Next.js (dynamic JS); Playwright executes full JS runtime |
| **Embedding Model** | Dense Embeddings | `bge-small-en-v1.5` (HuggingFace, 384-dim) | `text-embedding-3-small` (OpenAI, 1536-dim) | High accuracy on financial text; runs locally without API cost |
| **Vector Database** | HNSW Vector Index | `ChromaDB` | `Qdrant`, `FAISS` | Easiest local dev setup; Qdrant preferred for production scale |
| **Sparse Search** | Lexical Index | `BM25Okapi` (rank-bm25 lib) | `Elasticsearch` | Lightweight in-process; Elasticsearch for enterprise-scale |
| **Reranker** | Cross-Encoder | `bge-reranker-base` (HuggingFace) | `Cohere Rerank API` | Open-source, extremely fast latency; adequate for short chunks |
| **LLM** | Text Generation | `Groq API` (Llama 3 8B) | `GPT-4o` (OpenAI API), `Claude 3.5` | Groq provides ultra-low latency token generation ideal for real-time chat |
| **Orchestration** | RAG Framework | `LangChain` | `LlamaIndex`, `Haystack` | Mature ecosystem; LlamaIndex better for document-centric RAG |
| **Backend API** | REST Server | `FastAPI` (Python) | `Flask`, `Django REST` | Async support, native Pydantic validation, auto OpenAPI docs |
| **Frontend** | Chat UI | `Streamlit` (PoC) | `Next.js` (Production) | Streamlit for rapid prototype; Next.js for production-grade UI |
| **Evaluation** | RAG Quality | `Ragas` | `TruLens` | Finance-specific faithfulness metrics; both support LLM-as-judge |
| **Caching** | Response Cache | `Redis` | In-memory `dict` | TTL-based NAV data caching; avoid redundant API calls |
| **Containerization** | Deployment | `Docker` + `Docker Compose` | `Kubernetes` | Local dev with Docker Compose; K8s for horizontal scaling |

---

## 5. Deployment & Infrastructure Architecture

```mermaid
flowchart TB
    subgraph UserLayer["👤 Client Layer"]
        Browser["Web Browser\n(Investor / Advisor)"]
    end

    subgraph CDN["🌐 CDN / Reverse Proxy"]
        Nginx["Nginx Reverse Proxy\n+ TLS Termination"]
    end

    subgraph AppLayer["🐳 Application Containers (Docker Compose)"]
        UI_SVC["Frontend Service\nStreamlit / Next.js\n:3000"]
        API_SVC["FastAPI Backend\n:8000\n(Chat, Ingest, Funds APIs)"]
        CACHE["Redis Cache\n:6379\n(NAV TTL=1hr)"]
    end

    subgraph DataLayer["💾 Data & Index Layer"]
        VECTORDB["ChromaDB / Qdrant\n:8080\n(Vector Store + HNSW Index)"]
        RAWSTORE["Local JSON File Store\n(Scraped Fund Data)"]
    end

    subgraph ExternalAPIs["☁️ External Services"]
        GROQ["Groq API\n(Fast Llama 3 Inference)"]
        subgraph GrowwURLs["📄 Groww Data Sources (5 URLs Only)"]
            GU1["groww.in/.../hdfc-mid-cap-fund-direct-growth"]
            GU2["groww.in/.../hdfc-small-cap-fund-direct-growth"]
            GU3["groww.in/.../hdfc-gold-etf-fund-of-fund-direct-plan-growth"]
            GU4["groww.in/.../hdfc-multi-cap-fund-direct-growth"]
            GU5["groww.in/.../hdfc-large-cap-fund-direct-growth"]
        end
    end

    subgraph Scheduler["⏰ Scheduler"]
        CRON["Cron Job\nDaily 06:00 IST\n(Re-scrape + Re-index)"]
    end

    Browser --> Nginx
    Nginx --> UI_SVC
    UI_SVC --> API_SVC
    API_SVC --> CACHE
    API_SVC --> VECTORDB
    API_SVC --> GROQ
    API_SVC --> RAWSTORE
    CRON --> API_SVC
    API_SVC --> GU1
    API_SVC --> GU2
    API_SVC --> GU3
    API_SVC --> GU4
    API_SVC --> GU5
```

---

## 6. Non-Functional Requirements & System Guarantees

| Category | Target | Implementation Strategy |
| :--- | :--- | :--- |
| **Numeric Accuracy** | 100% | Hybrid BM25 retrieval for exact financial figures + post-generation numeric verifier |
| **Faithfulness** | > 95% | Strict system prompt rules; context-only generation; LLM temperature = 0.0 |
| **Answer Relevance** | > 90% | Cross-Encoder Reranking with `bge-reranker-large` to select maximally relevant chunks |
| **Response Latency** | < 2.0 seconds | Async FastAPI, Redis cache for repeated queries, streaming SSE token output |
| **Data Freshness** | Daily | Automated daily cron scraper at 06:00 IST to refresh all 5 Groww fund pages |
| **Corpus Coverage** | 5 HDFC Schemes | Bounded to: Mid Cap, Small Cap, Gold FoF, Multi Cap, Large Cap |
| **Evaluation** | Continuous | Ragas pipeline on 50-query golden test set measuring Faithfulness, Context Precision, Answer Relevance |
| **Scalability** | ~10K queries/day | Stateless FastAPI replicas behind Nginx; ChromaDB upgradeable to Qdrant for higher throughput |
