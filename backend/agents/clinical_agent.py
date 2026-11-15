
import os
import json
import re

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage,
)

from backend.agents.state import PharmacovigilanceState
from backend.agents.tools.agent_tools import (
    AVAILABLE_TOOLS,
    run_case_lookup,
)


load_dotenv(override=True)

MAX_TOOL_CALLS = 5


SYSTEM_PROMPT = """
You are the Clinical Assessment Agent in a pharmacovigilance system.

Your responsibilities:
1. Inspect the synthetic adverse event case.
2. Retrieve relevant evidence using available tools.
3. Assess seriousness using retrieved evidence and case facts.
4. Assess expectedness only when an approved package insert is available.
5. Never invent evidence, citations, patient facts or regulatory rules.

Available tools:
- corpus_search_tool
- clause_lookup_tool

Select tools dynamically based on the information required.

Safety rules:
- Hospitalisation is a seriousness criterion when the event
  results in or prolongs hospitalisation.
- Do not assume hospitalisation was caused by the event.
- Do not infer causality from timing alone.
- If the package insert is unavailable, expectedness is undetermined.
- Do not use clinical-trial regulations for marketed-product cases.
- Do not treat general guidance as a drug-specific package insert.
- Never invent citations.
- Use only exact chunk_id values returned by retrieval tools.

When you have gathered sufficient evidence, return ONLY valid JSON.
Do not wrap the JSON in Markdown code fences.

Required JSON structure:

{
  "reaction_description": "string",
  "seriousness": "serious | non_serious | undetermined",
  "expectedness": "expected | unexpected | undetermined",
  "causality": "certain | probable | possible | unlikely | unassessable | undetermined",
  "reasoning": "string",
  "evidence_references": [
    {
      "chunk_id": "exact retrieved chunk ID",
      "claim": "claim supported by this passage"
    }
  ]
}

If evidence is insufficient, explain the uncertainty in reasoning.
Never fabricate a citation to make the assessment appear complete.
"""


def get_clinical_model():
    """Initialize Gemini with the available retrieval tools."""

    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    )

    return model.bind_tools(AVAILABLE_TOOLS)


def extract_response_text(content):
    """Normalize different LangChain response content formats."""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))

        return "\n".join(parts).strip()

    return ""


def parse_clinical_assessment(content):
    """
    Parse the model's final response as JSON.

    Returns a dictionary or raises ValueError.
    """

    text = extract_response_text(content)

    if not text:
        raise ValueError("The clinical agent returned an empty response.")

    # Remove optional Markdown JSON fences.
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())

    try:
        assessment = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Clinical assessment is not valid JSON: {error}"
        ) from error

    if not isinstance(assessment, dict):
        raise ValueError("Clinical assessment must be a JSON object.")

    required_fields = [
        "reaction_description",
        "seriousness",
        "expectedness",
        "causality",
        "reasoning",
        "evidence_references",
    ]

    missing = [
        field for field in required_fields
        if field not in assessment
    ]

    if missing:
        raise ValueError(
            f"Clinical assessment is missing fields: {missing}"
        )

    if not isinstance(assessment["evidence_references"], list):
        raise ValueError("evidence_references must be a list.")

    if assessment["seriousness"] not in [
        "serious",
        "non_serious",
        "undetermined",
    ]:
        raise ValueError("Invalid seriousness value.")

    if assessment["expectedness"] not in [
        "expected",
        "unexpected",
        "undetermined",
    ]:
        raise ValueError("Invalid expectedness value.")

    return assessment


def collect_clinical_evidence(messages):
    """
    Extract retrieved passages from tool responses.

    The custom executor wraps successful results as:
    {
        "success": true,
        "result": [...]
    }
    """

    evidence = []
    seen_chunks = set()

    for message in messages:

        if not isinstance(message, ToolMessage):
            continue

        try:
            content = message.content

            if isinstance(content, list):
                content = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                )

            result = json.loads(content)

            if isinstance(result, dict):

                if result.get("success") is False:
                    continue

                result = result.get("result", result)

            if not isinstance(result, list):
                continue

            for item in result:

                if not isinstance(item, dict):
                    continue

                chunk_id = item.get("chunk_id")

                if not chunk_id or chunk_id in seen_chunks:
                    continue

                seen_chunks.add(chunk_id)
                evidence.append(item)

        except (json.JSONDecodeError, TypeError, ValueError):
            continue

    return evidence


def validate_assessment_citations(assessment, evidence):
    """Ensure every cited chunk exists in the retrieved evidence."""

    evidence_ids = {
        item.get("chunk_id")
        for item in evidence
        if item.get("chunk_id")
    }

    citations = assessment.get("evidence_references", [])

    if not citations:
        return False, ["The assessment contains no evidence references."]

    reasons = []

    for citation in citations:

        if not isinstance(citation, dict):
            reasons.append("An evidence reference has an invalid format.")
            continue

        chunk_id = citation.get("chunk_id")

        if not chunk_id or chunk_id not in evidence_ids:
            reasons.append(
                f"Citation {chunk_id} does not match retrieved evidence."
            )

        if not citation.get("claim"):
            reasons.append(
                f"Citation {chunk_id} has no associated claim."
            )

    return len(reasons) == 0, reasons


def clinical_agent_node(
    state: PharmacovigilanceState,
) -> dict:
    """
    Clinical Assessment Agent node.

    First invocation:
    - Validates case fields.
    - Initializes the conversation.

    Subsequent invocations:
    - Continues the tool-calling conversation.
    - Collects retrieved passages.
    - Parses the final structured assessment.
    - Validates citation IDs.
    """

    messages = list(state.get("messages", []))
    is_first_call = not messages

    extracted_fields = state.get("extracted_fields", {})
    missing_fields = state.get("missing_fields", [])

    if is_first_call:

        case = state.get("case_data", {})

        case_result = run_case_lookup(case)

        extracted_fields = case_result["case_fields"]
        missing_fields = case_result["missing_fields"]

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),

            HumanMessage(
                content=(
                    "Assess this synthetic adverse event case.\n\n"
                    f"Original case:\n{case}\n\n"
                    f"Validated fields:\n{extracted_fields}\n\n"
                    f"Missing fields:\n{missing_fields}"
                )
            ),
        ]

    elif not any(
        isinstance(message, SystemMessage)
        for message in messages
    ):

        messages.insert(
            0,
            SystemMessage(content=SYSTEM_PROMPT),
        )

    # Invoke Gemini.
    response = get_clinical_model().invoke(messages)

    # Preserve initial conversation history.
    messages_to_save = (
        messages + [response]
        if is_first_call
        else [response]
    )

    all_messages = messages + [response]

    clinical_evidence = collect_clinical_evidence(
        all_messages
    )

    result = {
        "messages": messages_to_save,
        "extracted_fields": extracted_fields,
        "missing_fields": missing_fields,
        "clinical_evidence": clinical_evidence,
        "current_agent": "clinical_assessment",
    }

    # If Gemini requested tools, wait for their execution.
    if getattr(response, "tool_calls", []):
        return result

    # Otherwise, parse its final assessment.
    try:

        assessment = parse_clinical_assessment(
            response.content
        )

        passed, citation_errors = validate_assessment_citations(
            assessment,
            clinical_evidence,
        )

        result["clinical_assessment"] = assessment

        if not passed:
            result["escalation_required"] = True
            result["escalation_reasons"] = citation_errors
            result["current_agent"] = "human_escalation"

    except ValueError as error:

        result["escalation_required"] = True
        result["escalation_reasons"] = [
            str(error)
        ]
        result["current_agent"] = "human_escalation"

    return result


def clinical_tool_router(
    state: PharmacovigilanceState,
) -> str:
    """Route the workflow based on the latest agent response."""

    if state.get("escalation_required", False):
        return "escalation"

    messages = state.get("messages", [])

    if not messages:
        return "escalation"

    last_message = messages[-1]

    requested_tools = getattr(
        last_message,
        "tool_calls",
        [],
    )

    if requested_tools:
        return "tools"

    return "assessment_complete"
