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
    k: int = 10,
):
    """
    Enhanced retrieval with more documents and better filtering.
    Retrieves top-k documents with relevance scoring.
    """
    index, mapping = load_knowledge_base(user_id)

    model = get_embedding_model()

    # Encode the query
    embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    # Search for top-k documents
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

    # Use top-5 most relevant documents (increased from 3)
    top_documents = documents[:5]
    
    # Include relevance scores in context for better LLM understanding
    context_parts = []
    for i, doc in enumerate(top_documents, 1):
        context_parts.append(
            f"Document {i} (relevance: {doc['similarity']:.3f}, file: {doc['filename']}):\n{doc['content']}"
        )
    
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""
You are a helpful assistant that answers questions based ONLY on the provided document context.
The context contains document sections ordered by relevance (highest similarity first).

Instructions:
1. Use the provided context to answer the question comprehensively
2. If multiple documents are relevant, synthesize information from all of them
3. If the answer is not clearly found in the documents, state "I could not find that information in your documents"
4. Do not make up information not present in the context
5. Be specific and reference the document filenames when possible

Conversation history:
{conversation_history}

Document context (ordered by relevance):
{context}

Question:
{question}

Answer:
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