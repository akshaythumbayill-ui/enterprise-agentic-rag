from functools import lru_cache
import gc

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Get the embedding model for semantic search.
    Using 'all-MiniLM-L6-v2' for good balance of speed and accuracy.
    For better accuracy, consider 'all-mpnet-base-v2' (slower but more accurate).
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    # Reduce memory footprint by not keeping the model in GPU
    model.max_seq_length = 256  # Limit sequence length for lower memory
    return model


def clear_model_from_memory():
    """Clear the embedding model from memory to free up resources."""
    global get_embedding_model
    get_embedding_model.cache_clear()
    gc.collect()