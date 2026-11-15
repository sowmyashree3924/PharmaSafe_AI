
from pathlib import Path

from langchain_community.vectorstores import FAISS

from backend.agents.retrieval.document_loader import load_corpus
from backend.agents.retrieval.chunker import split_documents
from backend.agents.retrieval.embeddings import get_embedding_model


PROJECT_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = PROJECT_ROOT / "data" / "faiss_index"


def build_vector_store():
    print("Loading documents...")
    documents = load_corpus()

    print("Creating page-aware chunks...")
    chunks = split_documents(documents)

    print(f"Total chunks: {len(chunks)}")

    print("Loading embedding model...")
    embeddings = get_embedding_model()

    print("Building FAISS index...")
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    INDEX_PATH.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(INDEX_PATH))

    print(f"FAISS index saved at: {INDEX_PATH}")

    return vector_store


def load_vector_store():
    embeddings = get_embedding_model()

    return FAISS.load_local(
        str(INDEX_PATH),
        embeddings,
        allow_dangerous_deserialization=True,
    )


if __name__ == "__main__":
    store = build_vector_store()

    query = "What makes an adverse event serious?"

    results = store.similarity_search(query, k=3)

    print("\n--- RETRIEVAL TEST ---")

    for result in results:
        print("\nDocument:", result.metadata["document_name"])
        print("PDF page:", result.metadata["page_number"])
        print("Scope:", result.metadata["scope"])
        print("Content:", result.page_content[:300])
