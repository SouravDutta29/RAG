from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"

class BGEEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        
    def embed_text(self, text: str):
        return self.model.encode(text, normalize_embeddings=True).tolist()
        
    def embed_batch(self, texts: list[str]):
        return self.model.encode(texts, normalize_embeddings=True).tolist()
