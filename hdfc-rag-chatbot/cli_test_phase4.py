import sys
from generator.guardrail import PromptGuard
from generator.prompt_builder import PromptBuilder
from generator.llm_engine import LLMEngine
from generator.verifier import FactVerifier
from generator.citation_injector import CitationInjector
from retriever.reranker import Reranker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    # Fix unicode encoding for windows console
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    # Allow passing query as command line argument or prompt interactively
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("HDFC Phase 4 Generator CLI Test")
        query = input("Enter a financial query: ")
        
    print(f"\n[1/6] Running Prompt Guard on query: '{query}'...")
    guard = PromptGuard()
    if not guard.check_safety(query):
        print("❌ Blocked by Prompt Guard: Unsafe query.")
        return
    print("✅ Guardrail passed.")
    
    print("\n[2/6] Retrieving and reranking context chunks (Phase 3)...")
    reranker = Reranker()
    chunks = reranker.retrieve_and_rerank(query, top_k_retrieve=10, top_k_final=5)
    print(f"✅ Retrieved {len(chunks)} top chunks.")
    
    print("\n[3/6] Building 4-block Financial Prompt...")
    builder = PromptBuilder()
    prompt = builder.build_prompt(query, chunks)
    
    print("\n[4/6] Generating Response from LLM (Streaming)...\n")
    llm = LLMEngine()
    full_response = ""
    for token in llm.generate_response_stream(prompt):
        print(token, end="", flush=True)
        full_response += token
        
    print("\n\n[5/6] Verifying Numeric Facts...")
    verifier = FactVerifier()
    verified_text = verifier.verify(full_response, chunks)
    if verified_text != full_response:
        print("⚠️ [CORRECTION APPLIED: Hallucinated numeric facts found!]")
        full_response = verified_text
    else:
        print("✅ Facts Verified.")
        
    print("\n[6/6] Injecting Citations and Disclaimer...")
    injector = CitationInjector()
    final_output = injector.inject_citations(full_response, chunks)
    
    print("\n" + "="*50)
    print("                 FINAL OUTPUT")
    print("="*50 + "\n")
    print(final_output)

if __name__ == "__main__":
    main()
