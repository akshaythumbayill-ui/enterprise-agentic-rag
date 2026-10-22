from functools import lru_cache

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Get the embedding model for semantic search.
    Using 'all-MiniLM-L6-v2' for good balance of speed and accuracy.
    For better accuracy, consider 'all-mpnet-base-v2' (slower but more accurate).
    """
    return SentenceTransformer("all-MiniLM-L6-v2")