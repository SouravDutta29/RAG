# Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
The **Mutual Fund FAQ Assistant** is a lightweight Retrieval-Augmented Generation (RAG)-based chatbot designed to answer objective, verifiable queries related to mutual funds using Groww as the reference product context. The assistant retrieves information exclusively from official public sources such as AMC (Asset Management Company) websites, AMFI, and SEBI. 

The system strictly avoids providing investment advice, opinions, or recommendations. Every response includes a clear source link and adheres to strict constraints around clarity, accuracy, and compliance.

## Objective
Design and implement a RAG-based assistant that:
- Answers factual queries about mutual fund schemes.
- Uses a curated corpus of official documents.
- Provides concise, source-backed responses.

## Target Users
- **Retail investors** comparing mutual fund schemes.
- **Customer support & content teams** handling repetitive mutual fund queries.

## Scope of Work

### 1. Corpus Definition
- **Selected AMC:** HDFC Mutual Fund
- **Schemes:** 3-5 diverse schemes (e.g., Mid-Cap, Small-Cap, Multi-Cap, Large-Cap, Gold FoF).
- **Sources:** 15–25 official public URLs (Scheme factsheets, KIM, SID, AMC FAQs, AMFI/SEBI guidance, etc.).

### 2. FAQ Assistant Requirements
- **Query Types:** Expense ratio, exit load, minimum SIP, ELSS lock-in, Riskometer classification, etc.
- **Formatting Constraints:**
  - Maximum 3 sentences per response.
  - Exactly one citation link per response.
  - Required footer: *"Last updated from sources: <date>"*

### 3. Refusal Handling
The assistant gracefully refuses non-factual or advisory queries (e.g., *"Should I invest in this fund?"*). 
- Refusals are polite and clearly worded.
- Reinforce the facts-only limitation.
- Provide a relevant educational link (e.g., AMFI/SEBI).

## Architecture (RAG Approach)
1. **Data Ingestion:** Web scraping and parsing module to extract HTML, key metrics (NAV, AUM, Expense Ratio), and holding tables.
2. **Hybrid Search Index:** Vector similarity search (embeddings) combined with keyword search (BM25) for accurate retrieval.
3. **Structured Context Injection:** Cleanly formatting retrieved fund context into prompt templates for LLM generation.
4. **LLM Engine:** Powered by GPT-4o / Claude 3.5 Sonnet / Llama-3 with financial guardrail prompts.

## Constraints & Compliance
- **Sources:** Only official public sources; no third-party blogs or aggregators.
- **Privacy:** No collection or storage of PII (PAN, Aadhaar, account numbers, etc.).
- **Content Restrictions:** No investment advice, performance comparisons, or return calculations.

## Disclaimer
> **Facts-only. No investment advice.**
> Past performance is not indicative of future returns.

Check the live RAG prototype here: https://groww-faq-assistant.streamlit.app/
---

*This project aims to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes accuracy over intelligence.*
