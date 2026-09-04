import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

documents = [
    "Employees receive 20 annual leave days",
    "Remote work is allowed 3 days per week",
    "Hotel reimbursement is limited to $200 per night",
    "Flights must be economy class"
]

model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(documents)

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(np.array(embeddings, dtype=np.float32))

print("Vectors stored:", index.ntotal)

faiss.write_index(index, "enterprise.index")

print("Index saved successfully")