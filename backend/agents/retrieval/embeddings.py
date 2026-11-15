
from langchain_huggingface import HuggingFaceEmbeddings


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


if __name__ == "__main__":
    model = get_embedding_model()

    test_text = "Hospitalisation is a criterion for a serious adverse event."

    vector = model.embed_query(test_text)

    print("Embedding model:", MODEL_NAME)
    print("Vector dimensions:", len(vector))
    print("First five values:", vector[:5])
