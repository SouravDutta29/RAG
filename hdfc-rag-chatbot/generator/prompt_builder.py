from typing import List, Dict, Any

class PromptBuilder:
    def __init__(self):
        self.system_prompt = """You are an expert financial advisor AI for HDFC Mutual Funds.
You must answer the user's queries strictly using the provided context chunks.
Do NOT use external knowledge. Do NOT hallucinate numeric figures.
If the context does not contain the answer, you must clearly state: "I don't know based on the provided context."
"""
        self.rules_prompt = """RULES:
1. All numeric figures (NAV, AUM, percentages) MUST be copied verbatim from the context.
2. If comparing funds, output a Markdown table with the funds as rows and metrics as columns.
3. Be concise and professional.
"""

    def build_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        context_blocks = []
        for i, chunk in enumerate(chunks):
            # Format each chunk nicely
            meta = chunk.get("metadata", {})
            scheme = meta.get("scheme_name", "Unknown Scheme")
            section = meta.get("section", "Unknown Section")
            
            block = f"--- Chunk {i+1} ---\nScheme: {scheme}\nSection: {section}\nContent:\n{chunk['content']}\n"
            context_blocks.append(block)
            
        context_str = "\n".join(context_blocks)
        
        full_prompt = f"{self.system_prompt}\n\n{self.rules_prompt}\n\nCONTEXT:\n{context_str}\n\nUSER QUERY:\n{query}"
        return full_prompt
