import os
import logging
from typing import Generator
from groq import Groq
from groq import RateLimitError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMEngine:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            api_key = "mock_key"
        self.client = Groq(api_key=api_key)
        self.model = "qwen/qwen3.6-27b"

    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    def _create_stream(self, prompt: str):
        """Make the API call. If a 429 RateLimitError is thrown, tenacity will catch and retry."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            stream=True
        )

    def generate_response_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Yields tokens for Server-Sent Events (SSE) streaming.
        """
        if self.client.api_key == "mock_key":
            logger.warning("Using mock GROQ_API_KEY. LLMEngine bypass enabled.")
            mock_resp = "This is a mock response because no API key was provided. HDFC Mid Cap NAV is 235.87."
            for word in mock_resp.split():
                yield word + " "
            return

        try:
            stream = self._create_stream(prompt)
            in_think = False
            buffer = ""
            for chunk in stream:
                token = chunk.choices[0].delta.content
                if not token:
                    continue
                    
                buffer += token
                
                while True:
                    if not in_think:
                        think_start = buffer.find("<think>")
                        if think_start != -1:
                            if think_start > 0:
                                yield buffer[:think_start]
                            buffer = buffer[think_start + len("<think>"):]
                            in_think = True
                        else:
                            last_lt = buffer.rfind("<")
                            if last_lt != -1 and "<think>".startswith(buffer[last_lt:]):
                                if last_lt > 0:
                                    yield buffer[:last_lt]
                                buffer = buffer[last_lt:]
                                break
                            else:
                                yield buffer
                                buffer = ""
                                break
                    else:
                        think_end = buffer.find("</think>")
                        if think_end != -1:
                            buffer = buffer[think_end + len("</think>"):]
                            if buffer.startswith("\n"):
                                buffer = buffer[1:]
                            in_think = False
                        else:
                            last_lt = buffer.rfind("<")
                            if last_lt != -1 and "</think>".startswith(buffer[last_lt:]):
                                buffer = buffer[last_lt:]
                            else:
                                buffer = ""
                            break
                            
            if buffer and not in_think:
                yield buffer
                
        except Exception as e:
            logger.error(f"LLM Engine error: {e}")
            yield f"\n[Error generating response: {str(e)}]"

    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    def generate_response(self, prompt: str) -> str:
        """
        Generates a full response synchronously (used for testing).
        """
        if self.client.api_key == "mock_key":
            return "This is a mock response because no API key was provided. HDFC Mid Cap NAV is 235.87."
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            stream=False
        )
        response_text = response.choices[0].message.content
        import re
        response_text = re.sub(r'<think>.*?</think>\n?', '', response_text, flags=re.DOTALL)
        return response_text
