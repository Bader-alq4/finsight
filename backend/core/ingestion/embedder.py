# Converts chunk text into 1536-dimensional vectors using the OpenAI embeddings API

import time
from openai import OpenAI
from backend.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def embed_batch(texts, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = client.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"  Embedding error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
    raise Exception("Embedding failed after all retries")

def embed_chunks(chunks, batch_size=100):
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]

        print(f"  Embedding batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}...")
        embeddings = embed_batch(texts)
        all_embeddings.extend(embeddings)

        time.sleep(0.1)

    return all_embeddings