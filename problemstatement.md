# Project Problem Statement: Financial RAG Chatbot for HDFC Mutual Funds

## 1. Executive Summary
The goal of this project is to build an intelligent, domain-specific Retrieval-Augmented Generation (RAG) chatbot designed to answer investor queries regarding specific HDFC Mutual Fund schemes hosted on Groww. The system will ingest, index, and retrieve accurate financial metadata, NAV history, expense ratios, portfolio holdings, and scheme details to deliver grounded, hallucination-free financial insights to end users.

---

## 2. Target Mutual Funds & Data Sources

The RAG system will be specifically configured and knowledge-grounded using data scraped/ingested from the following Groww mutual fund resources:

1. **HDFC Mid-Cap Opportunities Fund Direct-Growth**
   - **URL:** [https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
   - **Category:** Equity - Mid Cap
2. **HDFC Small Cap Fund Direct-Growth**
   - **URL:** [https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)
   - **Category:** Equity - Small Cap
3. **HDFC Gold ETF Fund of Fund Direct-Plan Growth**
   - **URL:** [https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth)
   - **Category:** Commodities / Fund of Funds (Gold)
4. **HDFC Multi Cap Fund Direct-Growth**
   - **URL:** [https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth](https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth)
   - **Category:** Equity - Multi Cap
5. **HDFC Large Cap Fund Direct-Growth**
   - **URL:** [https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)
   - **Category:** Equity - Large Cap / Top 100

---

## 3. Knowledge Base Corpus Definition & Schema Specification

### 3.1 Corpus Scope & Knowledge Boundaries
The knowledge corpus for the RAG chatbot is strictly bounded to the factual content extracted from the 5 target HDFC mutual fund URLs. The corpus is structured into structured JSON documents and semantic Markdown chunks prior to vector embedding.

### 3.2 Corpus Taxonomy & Data Schema
Each mutual fund scheme within the corpus is parsed into 5 core document categories:

| Category Module | Target Data Fields Extracted | Example Source Content |
| :--- | :--- | :--- |
| **1. Scheme Metadata** | Fund Name, AMC Name (`HDFC Mutual Fund`), Category, Risk Rating, Rating (Stars), Source URL | `HDFC Mid Cap Fund Direct Growth`, `Equity - Mid Cap`, `5-Star Rating` |
| **2. Key Financial Indicators (KFI)** | Latest NAV (Date & Price), Fund Size / AUM (in ₹ Cr), Minimum SIP Investment (₹), Expense Ratio (%) | `NAV: ₹235.87`, `AUM: ₹1,05,142.69 Cr`, `Min SIP: ₹100`, `Expense Ratio: 0.75%` |
| **3. Historical Returns & Performance** | 1D Return %, 1Y, 3Y, 5Y, and Annualized Return %, SIP Calculator Historical Projections | `3Y Annualized: +20.30%`, `1D: +0.23%`, `SIP ₹5,000/mo over 3 yrs = ₹2,19,230` |
| **4. Asset Allocation & Portfolio** | Equity/Debt/Cash split %, Top Sector Exposure %, Top 10 Stock Holdings (% weighting) | `Equity: 92.4%`, `Financials: 24.1%`, `Top Holdings: Indian Hotels, Max Healthcare` |
| **5. Scheme Info & Exit Load** | Exit Load rules, Lock-in period, Benchmark Index, Fund Manager Details, Tax Implications | `Exit Load: 1% if redeemed within 1 year`, `Benchmark: NIFTY Midcap 150 TRI` |

### 3.3 Metadata Schema per Vector Chunk
Every text chunk stored in the Vector Index must attach the following metadata JSON payload:

```json
{
  "scheme_id": "hdfc-mid-cap-fund-direct-growth",
  "scheme_name": "HDFC Mid Cap Fund Direct Growth",
  "category": "Equity - Mid Cap",
  "data_section": "Key Financial Indicators",
  "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  "nav_date": "2026-08-18",
  "last_updated": "2026-08-19T00:12:00Z"
}
```

---

## 4. Background & Current Challenges
- **Context:** Retail investors often struggle to compare mutual funds, analyze risk-return profiles, understand expense ratios, and inspect asset allocations across different market cap categories (Mid-Cap, Small-Cap, Multi-Cap, Large-Cap, Gold FoF).
- **Pain Points:** 
  - Generic LLMs lack up-to-date NAV rates, fund sizes (AUM), exit loads, and holding compositions.
  - Generic LLMs tend to hallucinate precise numeric values (e.g., returns %, expense ratios).
  - Manual comparison across multiple web pages is tedious for investors.
- **Target Users:** Retail investors, financial advisors, and research analysts looking for instant, verifiable financial Q&A and fund comparisons.

---

## 5. Project Objectives & Scope

### 5.1 Primary Goals
- [ ] **Data Ingestion:** Web scrape and parse web content and metadata from the target 5 HDFC mutual fund Groww pages.
- [ ] **Grounded RAG Pipeline:** Build a RAG indexing pipeline storing fund overview, performance metrics, holding analysis, minimum SIP amounts, AUM, and risk profiles.
- [ ] **Comparative Q&A:** Enable side-by-side fund comparisons (e.g., *"Compare risk vs returns between HDFC Mid-Cap and HDFC Small-Cap"*).
- [ ] **Factuality & Citation:** Provide source links and timestamps for all retrieved fund metrics to prevent financial hallucination.

### 5.2 Key Features & Capabilities
1. **Financial Web Scraping / Parsing:** Web scraping module to extract HTML, key metrics (NAV, AUM, Expense Ratio, Min SIP), and holding tables from target Groww URLs.
2. **Hybrid Search Index:** Vector similarity search (embeddings) combined with keyword search (BM25) for accurate retrieval of specific numerical queries (e.g., *"What is the expense ratio of HDFC Gold ETF FoF?"*).
3. **Structured Financial Context Injection:** Formatting retrieved fund context cleanly into prompt templates for LLM generation.
4. **Interactive Chat Interface / API:** Conversational interface supporting follow-up questions and fund comparison tables.

---

## 6. Technical Requirements & Architecture

### 6.1 Ingestion & Indexing Pipeline
- **Data Source Integrator:** HTML / JSON scraping scripts for the 5 target Groww URLs.
- **Chunking Strategy:** 
  - Semantic Chunking by Fund Attribute (Overview, Performance, Holdings, Risk, Fees).
  - Metadata Tagging: `fund_name`, `category`, `url`, `fund_house: HDFC`.
- **Embedding Model:** Open-source or API embeddings (e.g., `text-embedding-3-small` or `bge-small-en-v1.5`).
- **Vector Store:** Vector database (e.g., ChromaDB, FAISS, or Qdrant).

### 6.2 Retrieval & Generation Pipeline
- **Search Strategy:** Hybrid Search (Dense Embeddings + Sparse BM25) + Cross-Encoder Reranking.
- **LLM Engine:** GPT-4o / Claude 3.5 Sonnet / Llama-3 with financial guardrail prompts.
- **Disclaimer Enforcement:** Mandatory automated disclaimer appending (*"Not financial advice. Past performance is not indicative of future returns."*).

---

## 7. Evaluation & Performance Metrics

| Metric | Target / Benchmark | Description |
| :--- | :--- | :--- |
| **Numeric Accuracy** | $100\%$ | Expense ratios, NAV, AUM, and min SIP values must match official source exactly |
| **Faithfulness** | $> 95\%$ | Answer is strictly derived from retrieved fund context |
| **Answer Relevance** | $> 90\%$ | Directly addresses the user's specific fund query |
| **Latency** | $< 2.0\text{ seconds}$ | End-to-end user response generation latency |

---

## 8. Development Roadmap
- [ ] **Phase 1: Scraper & Knowledge Base Setup** — Scrape data from 5 Groww URLs and construct vector index.
- [ ] **Phase 2: RAG Pipeline Development** — Implement hybrid retrieval, financial prompt templates, and citation tracking.
- [ ] **Phase 3: Chat Interface & Verification** — Develop UI/API, test sample investor queries, and validate accuracy across all 5 funds.
