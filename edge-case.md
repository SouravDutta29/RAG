# Edge Cases & Corner Scenarios: HDFC Mutual Funds RAG Chatbot

This document outlines potential edge cases, corner scenarios, and failure modes across the 5 layers of the system architecture defined in [Architecture.md](file:///c:/Users/Windows/Desktop/RAG/Architecture.md) and [ImplementationPlan.md](file:///c:/Users/Windows/Desktop/RAG/ImplementationPlan.md). It also provides mitigation strategies for each scenario.

---

## Layer 1: Data Ingestion & ETL Layer (Playwright Scraper)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **DOM Structure Drift** | Groww updates their UI layout, changing class names or the structure of the `__NEXT_DATA__` JSON. | Implement robust JSON path parsing with fallbacks. Set up a daily alert in the cron job if critical fields (NAV, AUM) resolve to `null`. |
| **CAPTCHA / Rate Limiting** | Groww blocks the headless Playwright scraper via Cloudflare or rate-limiting. | Introduce randomized sleep intervals between the 5 URL requests. Use rotating user-agent strings. If persistent, fall back to official AMC PDFs as a manual override. |
| **Missing Expected Data** | A specific fund page omits a typically standard field (e.g., no exit load rule is defined). | The JSON Normalizer must handle missing values gracefully using `None` or `"N/A"`. The Prompt Builder should be instructed not to hallucinate missing data. |
| **Stale Data on Target Site** | The Groww page itself has not updated the NAV for a public holiday/weekend. | Extract and index the `nav_date` string alongside the NAV value. The chatbot must explicitly state the date of the NAV (e.g., "As of 18 Aug, the NAV is..."). |

---

## Layer 2: Dual Indexing Pipeline (BGE + BM25)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Corrupted Index Updates** | The daily cron job fails halfway, leaving ChromaDB with stale data and BM25 with new data. | Implement atomic index updates. Write to a staging ChromaDB collection first, verify chunk counts, and then swap collection aliases. |
| **Metadata Tagging Failure** | A chunk is improperly tagged with the wrong `scheme_slug`. | Implement strict Pydantic validation before upserting into ChromaDB. Cross-reference the fund name string against a predefined Enum of the 5 supported HDFC funds. |

---

## Layer 3: Retrieval & Query Routing (RRF + Cross-Encoder)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Out-of-Bounds Queries** | User asks about a fund not in the 5 bounds (e.g., "What is the NAV of SBI Small Cap?"). | The Query Router should detect out-of-corpus entities and immediately return a hardcoded fallback: "I am specialized only in the 5 HDFC schemes. I cannot answer queries about SBI Small Cap." |
| **Ambiguous Queries** | User asks "What is the NAV today?" without specifying *which* of the 5 HDFC funds. | The Prompt should instruct the LLM to ask for clarification: "Could you specify which fund's NAV you are looking for? (e.g., HDFC Mid Cap or HDFC Small Cap)." |
| **Vocabulary Mismatch** | User asks for "MER" or "Management Fees" instead of "Expense Ratio". | BM25 sparse search will fail, but Dense Vector search (BGE embeddings) will capture the semantic intent and retrieve the chunk. The RRF fusion gracefully handles this. |
| **Complex Multi-Hop Comparisons** | "Which fund has a higher AUM than HDFC Mid Cap but a lower expense ratio than HDFC Small Cap?" | The router must categorize this as `COMPARATIVE` and force top-K retrieval of *all* 5 funds' Key Financial Indicators chunks to ensure the LLM has all the data to compute the logic. |

---

## Layer 4: LLM Generation & Financial Guardrails (Groq API + Llama 3)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Numeric Verifier False Positives** | The LLM writes "1 Lakh" instead of "100,000" or "$235.8" instead of "235.87", causing the verbatim Fact Verifier to fail and reject a correct answer. | The prompt must strictly instruct the LLM: *"Copy numeric values exactly as they appear in the text. Do not round, abbreviate, or convert currencies."* |
| **Entity Mix-ups (Hallucination)** | The LLM retrieves correct NAVs but assigns the Mid Cap NAV to the Small Cap fund in its text response. | The Fact Verifier must be context-aware: it should map the numeric value to the specific `scheme_name` metadata of the chunk it came from, rejecting responses where the fund name and value don't match the source chunk. |
| **Groq API Context Limit** | A highly comparative query pulls too many large chunks, exceeding the Llama 3 context window. | The Cross-Encoder reranker strictly truncates the context to the Top-5 chunks (max ~2500 tokens), guaranteeing it never exceeds standard LLM context windows. |

---

## Layer 5: API Backend & User Interface

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Cache Stampede** | 1,000 users ask "What is the NAV of HDFC Mid Cap?" exactly when the 1-hour Redis cache expires. | Implement cache locking/debouncing in FastAPI so only the first request queries the RAG pipeline while the other 999 wait for the cache to populate. |
| **Streaming Interruptions** | The user's browser disconnects while the Groq API is halfway through streaming the SSE tokens. | The FastAPI endpoint must catch `ClientDisconnect` exceptions and gracefully terminate the Groq API stream to prevent zombie processes. |
| **UI Table Parsing Failure** | The LLM generates a malformed Markdown table for a comparative query. | The Streamlit/Next.js frontend should use a resilient Markdown parser (e.g., `react-markdown` with `remark-gfm`) that handles missing pipes `|` gracefully. |
