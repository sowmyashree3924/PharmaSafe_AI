
import json

from langchain_core.messages import ToolMessage

from backend.agents.clinical_agent import (
    collect_clinical_evidence,
)


def test_evidence_collection():

    retrieved_passage = {
        "chunk_id": "DOC002_PAGE_32_CHUNK_001",
        "document_id": "DOC002",
        "document_name": "IPC Pharmacovigilance Guidance",
        "scope": "marketed_product",
        "pdf_page": 32,
        "passage": "Hospitalisation is a seriousness criterion.",
    }

    tool_message = ToolMessage(
        content=json.dumps({
            "success": True,
            "result": [
                retrieved_passage,
                retrieved_passage,
            ],
        }),
        tool_call_id="test-1",
    )

    evidence = collect_clinical_evidence(
        [tool_message]
    )

    assert len(evidence) == 1

    assert (
        evidence[0]["chunk_id"]
        == retrieved_passage["chunk_id"]
    )

    print("PASS: Tool evidence collected.")
    print("PASS: Duplicate chunks removed.")
    print("Collected evidence:", len(evidence))


if __name__ == "__main__":
    test_evidence_collection()
