

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


PAGE_PATTERN = re.compile(r"--- PAGE (\d+) ---")


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[Document]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []

    for document in documents:
        pages = PAGE_PATTERN.split(document.page_content)

        # The split result alternates: text before marker, page number, page text.
        for index in range(1, len(pages), 2):
            page_number = int(pages[index])
            page_text = pages[index + 1].strip()

            if not page_text:
                continue

            page_document = Document(
                page_content=page_text,
                metadata={
                    **document.metadata,
                    "page_number": page_number,
                },
            )

            page_chunks = splitter.split_documents([page_document])

            for chunk_index, chunk in enumerate(page_chunks):
                chunk.metadata["chunk_id"] = (
                    f"{document.metadata['document_id']}"
                    f"_PAGE_{page_number}_CHUNK_{chunk_index:03d}"
                )
                all_chunks.append(chunk)

    return all_chunks


if __name__ == "__main__":
    from backend.agents.retrieval.document_loader import load_corpus

    documents = load_corpus()
    chunks = split_documents(documents)

    print(f"Loaded documents: {len(documents)}")
    print(f"Generated page-aware chunks: {len(chunks)}")

    for chunk in chunks[:5]:
        print("\n--- CHUNK ---")
        print("ID:", chunk.metadata["chunk_id"])
        print("Document:", chunk.metadata["document_name"])
        print("PDF page:", chunk.metadata["page_number"])
        print("Scope:", chunk.metadata["scope"])
        print("Content:", chunk.page_content[:200])
