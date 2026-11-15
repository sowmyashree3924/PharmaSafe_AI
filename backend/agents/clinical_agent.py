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


# --------------------------------------------------
# Prompt version selection
# --------------------------------------------------

PROMPT_VERSION = os.getenv("CLINICAL_PROMPT_VERSION", "v2")

if PROMPT_VERSION == "v1":
    from prompts.v1.clinical_assessment import (
        CLINICAL_ASSESSMENT_PROMPT,
    )
elif PROMPT_VERSION == "v2":
    from prompts.v2.clinical_assessment import (
        CLINICAL_ASSESSMENT_PROMPT,
    )
else:
    raise ValueError(
        f"Unsupported clinical prompt version: {PROMPT_VERSION}"
    )

SYSTEM_PROMPT = CLINICAL_ASSESSMENT_PROMPT


# --------------------------------------------------
# Gemini model
# --------------------------------------------------

def get_clinical_model():
    """Initialize Gemini with the available retrieval tools."""

    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    )

    return model.bind_tools(AVAILABLE_TOOLS)


# --------------------------------------------------
# Response extraction
# --------------------------------------------------

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


# --------------------------------------------------
# Clinical assessment parsing
# --------------------------------------------------

def parse_clinical_assessment(content):
    """
    Parse the model's final response as JSON.

    Returns a dictionary or raises ValueError.
    """

    text = extract_response_text(content)

    if not text:
        raise ValueError(
            "The clinical agent returned an empty response."
        )

    # Remove optional Markdown JSON fences.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )

    text = re.sub(r"\s*```$", "", text.strip())

    try:
        assessment = json.loads(text)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Clinical assessment is not valid JSON: {error}"
        ) from error

    if not isinstance(assessment, dict):
        raise ValueError(
            "Clinical assessment must be a JSON object."
        )

    required_fields = [
        "reaction_description",
        "seriousness",
        "expectedness",
        "causality",
        "reasoning",
        "evidence_references",
    ]

    missing = [
        field
        for field in required_fields
        if field not in assessment
    ]

    if missing:
        raise ValueError(
            f"Clinical assessment is missing fields: {missing}"
        )

    if not isinstance(assessment["evidence_references"], list):
        raise ValueError(
            "evidence_references must be a list."
        )

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


# --------------------------------------------------
# Evidence collection
# --------------------------------------------------

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


# --------------------------------------------------
# Citation validation
# --------------------------------------------------

def validate_assessment_citations(assessment, evidence):
    """Ensure every cited chunk exists in the retrieved evidence."""

    evidence_ids = {
        item.get("chunk_id")
        for item in evidence
        if item.get("chunk_id")
    }

    citations = assessment.get("evidence_references", [])

    if not citations:
        return False, [
            "The assessment contains no evidence references."
        ]

    reasons = []

    for citation in citations:

        if not isinstance(citation, dict):
            reasons.append(
                "An evidence reference has an invalid format."
            )
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


# --------------------------------------------------
# Deterministic missing-data guard
# --------------------------------------------------

def build_missing_data_escalation(
    extracted_fields,
    missing_fields,
):
    """
    Escalate incomplete cases before invoking the LLM.

    The model must not infer or fabricate missing case information.
    """

    return {
        "extracted_fields": extracted_fields,
        "missing_fields": missing_fields,
        "clinical_evidence": [],
        "escalation_required": True,
        "escalation_reasons": [
            f"Required case information is missing: {field}"
            for field in missing_fields
        ],
        "reporting_route": "human_review",
        "current_agent": "human_escalation",
    }


# --------------------------------------------------
# Clinical Assessment Agent
# --------------------------------------------------

def clinical_agent_node(
    state: PharmacovigilanceState,
) -> dict:
    """
    Clinical Assessment Agent node.

    First invocation:
    - Validates case fields.
    - Escalates incomplete cases before invoking Gemini.
    - Initializes the conversation for complete cases.

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

    # ----------------------------------------------
    # First invocation: validate the submitted case
    # ----------------------------------------------

    if is_first_call:

        case = state.get("case_data", {})

        case_result = run_case_lookup(case)

        extracted_fields = case_result["case_fields"]
        missing_fields = case_result["missing_fields"]

        # IMPORTANT:
        # Do not invoke Gemini if required information
        # is missing from the submitted case.

        if missing_fields:
            return build_missing_data_escalation(
                extracted_fields,
                missing_fields,
            )

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

    # ----------------------------------------------
    # Invoke Gemini
    # ----------------------------------------------

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

    # ----------------------------------------------
    # Handle tool calls
    # ----------------------------------------------

    if getattr(response, "tool_calls", []):
        return result

    # ----------------------------------------------
    # Parse final clinical assessment
    # ----------------------------------------------

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


# --------------------------------------------------
# Workflow routing
# --------------------------------------------------

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


# Backward compatibility for older tests and integrations.
clinical_assessment_agent = clinical_agent_node
