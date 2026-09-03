import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

try:
    models = client.models.list()
    print("Available Models:")
    for m in models.data:
        print(f"- {m.id}")
except Exception as e:
    print(f"Error fetching models: {e}")

try:
    response = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10
    )
    print("\nQwen test success:", response.choices[0].message.content)
except Exception as e:
    print("\nQwen test failed:", type(e).__name__, e)
