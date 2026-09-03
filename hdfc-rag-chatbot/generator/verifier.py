import re
from typing import List, Dict, Any

class FactVerifier:
    def __init__(self):
        # Regex to match numeric figures: decimals (like 235.87), percentages (like 12.5%), 
        # currency/large numbers (like 11197.0455 or 11,197)
        self.numeric_pattern = re.compile(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b')

    def verify(self, generated_text: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Extracts all numeric entities from the generated text and verifies
        that they appear verbatim in at least one of the context chunks.
        If any fail, returns a canned fallback message.
        """
        # Combine all context into one giant string for easy verbatim substring checking
        full_context = " ".join([c["content"] for c in context_chunks])
        
        # Extract all numbers from generated text
        numerics = self.numeric_pattern.findall(generated_text)
        
        # Remove small integers that might just be list numbers or general words (like 1, 2, 3)
        # We only really care about verifying actual data figures.
        significant_numerics = [n for n in numerics if len(n.replace('.', '').replace(',', '')) >= 2 or '.' in n]

        for num in significant_numerics:
            if num not in full_context:
                # Verification failed! The LLM hallucinated a number.
                return "Verified data not available in the knowledge base for this figure."
                
        return generated_text
