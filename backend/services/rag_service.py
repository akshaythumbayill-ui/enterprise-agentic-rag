import json

import faiss
import numpy as np

from .embedding_service import get_embedding_model
from .index_service import get_knowledge_base_paths
from .llm import ask_llm


def load_knowledge_base(user_id: int):
    paths = get_knowledge_base_paths(user_id)

    if (
        not paths["index_path"].exists()
        or not paths["mapping_path"].exists()
    ):
        raise FileNotFoundError(
            "Your knowledge base is empty. Upload a PDF first."
        )

    index = faiss.read_index(str(paths["index_path"]))

    with paths["mapping_path"].open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        mapping = json.load(file)

    return index, mapping


def retrieve_documents(
    question: str,
    user_id: int,
    k: int = 4,
):
    index, mapping = load_knowledge_base(user_id)

    model = get_embedding_model()

    embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    distances, indices = index.search(
        np.asarray(embedding, dtype=np.float32),
        min(k, index.ntotal),
    )

    # Return documents with relevance scores
    documents_with_scores = []
    for distance, index_id in zip(distances[0], indices[0]):
        if index_id != -1:
            doc = mapping[int(index_id)]
            # Convert distance to similarity score (cosine distance to similarity)
            similarity = 1 - distance
            documents_with_scores.append({
                **doc,
                "similarity": float(similarity),
                "distance": float(distance),
            })

    # Sort by similarity (descending)
    documents_with_scores.sort(key=lambda x: x["similarity"], reverse=True)

    return documents_with_scores


def answer_question(
    question: str,
    user_id: int,
    conversation_history: str = "",
):
    try:
        documents = retrieve_documents(question, user_id)
    except FileNotFoundError:
        return {
            "question": question,
            "answer": "No indexed documents are available. Upload a PDF to ask document questions.",
            "sources": [],
        }

    # Use top-k most relevant documents
    top_documents = documents[:3]
    
    # Include relevance scores in context for better LLM understanding
    context_parts = []
    for i, doc in enumerate(top_documents, 1):
        context_parts.append(
            f"Source {i} (relevance: {doc['similarity']:.2f}, file: {doc['filename']}):\n{doc['content']}"
        )
    
    context = "\n\n".join(context_parts)

    prompt = f"""
Use only the company-document context as the factual source.
Context is ordered by relevance (highest similarity first).

Conversation history:
{conversation_history}

Company-document context:
{context}

Question:
{question}

If the answer is unavailable in the documents, say:
"I could not find that information in your documents."

Provide a comprehensive answer based on the most relevant document sections.
"""

    answer = ask_llm(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "id": document["id"],
                "filename": document["filename"],
                "content": document["content"],
                "similarity": document["similarity"],
            }
            for document in top_documents
        ],
    }