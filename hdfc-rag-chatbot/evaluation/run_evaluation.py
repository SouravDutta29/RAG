import os
import sys
import json
import argparse
import time
import requests
from pathlib import Path

# Setup path to import local modules
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from retriever.reranker import Reranker
from generator.prompt_builder import PromptBuilder
from generator.llm_engine import LLMEngine
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def judge_answer(question, answer, contexts, ground_truth):
    """
    Uses Llama-3 to act as an AI judge and score the answer.
    """
    judge_prompt = f"""You are an impartial AI judge evaluating a chatbot's response.
    
Question: {question}
Ground Truth Expected Answer: {ground_truth}
Contexts Provided to Chatbot: {contexts}
Chatbot's Answer: {answer}

Evaluate the Chatbot's Answer based on the following criteria:
1. Faithfulness: Is the answer entirely supported by the Contexts? (1 for Yes, 0 for No)
2. Relevancy: Does the answer address the Question? (1 for Yes, 0 for No)
3. Correctness: Does the answer align with the Ground Truth? (1 for Yes, 0 for No)

Respond ONLY with a valid JSON object. Do not include any markdown formatting, backticks, or explanation.
{{
    "faithfulness": 1,
    "relevancy": 1,
    "correctness": 1
}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": judge_prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            scores = json.loads(content)
            return scores
    except Exception as e:
        print(f"Failed to judge: {e}")
        
    return {"faithfulness": 0, "relevancy": 0, "correctness": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of queries to evaluate. Set to 50 for full run.")
    args = parser.parse_args()

    print("Initializing RAG components...")
    reranker = Reranker()
    prompt_builder = PromptBuilder()
    llm = LLMEngine()

    print("Loading test set...")
    with open("evaluation/golden_test_set.json", "r") as f:
        test_queries = json.load(f)

    test_queries = test_queries[:args.limit]
    results = []
    
    total_faithfulness = 0
    total_relevancy = 0
    total_correctness = 0

    print(f"Running Custom Evaluation Pipeline for {len(test_queries)} queries...")
    for i, item in enumerate(test_queries):
        q = item["query"]
        print(f"[{i+1}/{len(test_queries)}] Query: {q}")
        
        # 1. Retrieval
        top_chunks = reranker.retrieve_and_rerank(q)
        contexts = [c["text"] for c in top_chunks]
        
        # 2. Generation
        prompt = prompt_builder.build_prompt(q, top_chunks)
        answer = ""
        for token in llm.generate_response_stream(prompt):
            answer += token
            
        # 3. AI Judging
        scores = judge_answer(q, answer, contexts, item["ground_truth"])
        
        total_faithfulness += scores.get("faithfulness", 0)
        total_relevancy += scores.get("relevancy", 0)
        total_correctness += scores.get("correctness", 0)
        
        results.append({
            "question": q,
            "answer": answer,
            "scores": scores
        })
        time.sleep(1) # Prevent API rate limits

    # Calculate final averages
    n = len(test_queries)
    avg_faithfulness = (total_faithfulness / n) * 100
    avg_relevancy = (total_relevancy / n) * 100
    avg_correctness = (total_correctness / n) * 100

    print("\n=== EVALUATION RESULTS ===")
    print(f"Faithfulness Score: {avg_faithfulness:.1f}%")
    print(f"Relevancy Score:    {avg_relevancy:.1f}%")
    print(f"Correctness Score:  {avg_correctness:.1f}%")

    with open("evaluation/results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("\nResults saved to evaluation/results.json")

if __name__ == "__main__":
    main()
