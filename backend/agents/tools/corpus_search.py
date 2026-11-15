
from typing import Optional

from backend.agents.retrieval.vector_store import load_vector_store


def search_corpus(
    query: str,
    scope: Optional[str] = None,
    k: int = 5,
) -> list[dict]:

    vector_store = load_vector_store()

    filters = {"scope": scope} if scope else None

    results = vector_store.similarity_search(
        query=query,
        k=k,
        filter=filters,
    )

    evidence = []

    for document in results:
        evidence.append({
            "chunk_id": document.metadata["chunk_id"],
            "document_id": document.metadata["document_id"],
            "document_name": document.metadata["document_name"],
            "scope": document.metadata["scope"],
            "pdf_page": document.metadata["page_number"],
            "passage": document.page_content,
        })

    return evidence


if __name__ == "__main__":
    results = search_corpus(
        query="Hospitalisation as a seriousness criterion for adverse events",
        scope="marketed_product",
        k=3,
    )

    for item in results:
        print("\n----------------------------")
        print("Document:", item["document_name"])
        print("Page:", item["pdf_page"])
        print("Scope:", item["scope"])
        print("Chunk:", item["chunk_id"])
        print("Evidence:", item["passage"][:400])
