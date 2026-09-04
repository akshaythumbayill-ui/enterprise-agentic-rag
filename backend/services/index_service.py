import json
from pathlib import Path

import faiss
import numpy as np

from .embedding_service import get_embedding_model

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def get_knowledge_base_paths(user_id: int):
    user_data_dir = DATA_DIR / "users" / str(user_id)

    return {
        "data_dir": user_data_dir,
        "index_path": user_data_dir / "enterprise.index",
        "mapping_path": user_data_dir / "document_mapping.json",
    }


def build_index(documents: list[dict], user_id: int):
    if not documents:
        raise ValueError("No documents were supplied to build the index.")

    paths = get_knowledge_base_paths(user_id)
    paths["data_dir"].mkdir(parents=True, exist_ok=True)

    normalized_documents = [
        {
            "id": index,
            "filename": document["filename"],
            "content": document["content"],
        }
        for index, document in enumerate(documents)
    ]

    texts = [
        document["content"]
        for document in normalized_documents
    ]

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(paths["index_path"]))

    with paths["mapping_path"].open("w", encoding="utf-8") as file:
        json.dump(
            normalized_documents,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return {
        "documents_indexed": len(normalized_documents),
        "index_path": str(paths["index_path"]),
    }

def delete_knowledge_base(user_id: int):
    paths = get_knowledge_base_paths(user_id)

    paths["index_path"].unlink(missing_ok=True)
    paths["mapping_path"].unlink(missing_ok=True)