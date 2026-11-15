
from pathlib import Path
from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DOCUMENTS = [
    {
        "document_id": "DOC001",
        "name": "New Drugs and Clinical Trials Rules 2019",
        "path": "docs/planning/extracted_text/New Drugs and Clinical Trials Rules, 2019.txt",
        "document_type": "regulation",
        "scope": "clinical_trial",
    },
    {
        "document_id": "DOC002",
        "name": "Pharmacovigilance Guidance for Marketing Authorization Holders",
        "path": "docs/planning/extracted_text/Pharmacovigilance Guidance for Marketing Authorization Holders.txt",
        "document_type": "guidance",
        "scope": "marketed_product",
    },
    {
        "document_id": "DOC003",
        "name": "WHO-UMC Causality Assessment",
        "path": "docs/planning/extracted_text/WHO-UMC_Causality_Assessment.txt",
        "document_type": "reference",
        "scope": "causality_assessment",
    },
]


def load_corpus() -> list[Document]:
    documents = []

    for source in DOCUMENTS:
        file_path = PROJECT_ROOT / source["path"]

        if not file_path.exists():
            raise FileNotFoundError(f"Missing corpus file: {file_path}")

        text = file_path.read_text(encoding="utf-8")

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "document_id": source["document_id"],
                    "document_name": source["name"],
                    "document_type": source["document_type"],
                    "scope": source["scope"],
                    "source_path": source["path"],
                },
            )
        )

    return documents


if __name__ == "__main__":
    docs = load_corpus()

    print(f"Successfully loaded {len(docs)} documents.")

    for doc in docs:
        print(
            f"{doc.metadata['document_id']}: "
            f"{doc.metadata['document_name']} "
            f"({len(doc.page_content)} characters)"
        )
