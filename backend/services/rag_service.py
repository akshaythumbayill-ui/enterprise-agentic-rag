import json
import gc

import faiss
import numpy as np

from .embedding_service import get_embedding_model, clear_model_from_memory
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
    k: int = 10,  # Reduced from 15 to save memory
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

    # Clear embedding from memory
    del embedding
    gc.collect()

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

    # Use top-5 most relevant documents (reduced from 7 to save memory)
    top_documents = documents[:5]
    
    # Filter out low-relevance documents (similarity < 0.3)
    relevant_documents = [doc for doc in top_documents if doc['similarity'] >= 0.3]
    
    if not relevant_documents:
        return {
            "question": question,
            "answer": "I searched through your documents but couldn't find any relevant information to answer your question. Try rephrasing your question or upload more relevant documents.",
            "sources": [],
        }
    
    # Include relevance scores in context for better LLM understanding
    context_parts = []
    for i, doc in enumerate(relevant_documents, 1):
        context_parts.append(
            f"Document {i} (relevance: {doc['similarity']:.2%}, file: {doc['filename']}):\n{doc['content']}"
        )
    
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are an expert enterprise knowledge assistant. Your task is to answer questions accurately based ONLY on the provided document context.

CONTEXT INFORMATION:
- The context below contains document sections ordered by relevance (highest similarity first)
- Each document section includes its relevance score and source filename
- Higher relevance scores indicate better matches to the question

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer the question using ONLY the provided document context
2. If multiple documents contain relevant information, synthesize a comprehensive answer
3. Be specific and reference which document/file the information came from
4. If the answer is clearly stated in the documents, provide it directly
5. If the information is mentioned but requires interpretation, explain your reasoning
6. If the answer is NOT found in the documents, clearly state: "I could not find that specific information in your documents"
7. Do not make up information or use outside knowledge
8. Organize your answer with clear structure:
   - Start with a direct answer
   - Provide supporting details with document references
   - Use bullet points for multiple items
   - Use numbered lists for sequential information

CONVERSATION HISTORY (for context):
{conversation_history}

ANSWER:"""

    answer = ask_llm(prompt, temperature=0.1, max_tokens=2048)

    # Clear memory after processing
    gc.collect()

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
            for document in relevant_documents
        ],
    }
