from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

embedding = model.encode(
    "Remote work policy"
)

print(type(embedding))
print(len(embedding))
print(embedding[:10])