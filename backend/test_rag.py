from services.rag_service import retrieve_documents

docs = retrieve_documents(
    "How many vacation days do employees get?"
)

print(docs)