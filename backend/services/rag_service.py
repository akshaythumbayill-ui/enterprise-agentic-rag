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
    k: int = 2,
):
    index, mapping = load_knowledge_base(user_id)

    model = get_embedding_model()

    embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    _, indices = index.search(
        np.asarray(embedding, dtype=np.float32),
        min(k, index.ntotal),
    )

    return [
        mapping[int(index_id)]
        for index_id in indices[0]
        if index_id != -1
    ]


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

    context = "\n\n".join(
        f"Source: {document['filename']}\n{document['content']}"
        for document in documents
    )

    prompt = f"""
Use only the company-document context as the factual source.

Conversation history:
{conversation_history}

Company-document context:
{context}

Question:
{question}

If the answer is unavailable in the documents, say:
"I could not find that information in your documents."
"""

    answer = ask_llm(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "id": document["id"],
                "filename": document["filename"],
            }
            for document in documents
        ],
    }