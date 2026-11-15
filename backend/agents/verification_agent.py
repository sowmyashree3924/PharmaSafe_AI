
from backend.agents.state import PharmacovigilanceState


# Evidence scope rules
ALLOWED_MARKETED_PRODUCT_SCOPES = {
    "marketed_product",
}

# Keywords used for basic claim-to-passage checks.
# This is a deterministic screening layer, not an LLM entailment model.
CLAIM_KEYWORDS = {
    "hospitalisation": [
        "hospitalisation",
        "hospitalization",
        "inpatient",
    ],
    "seriousness": [
        "serious",
        "hospitalisation",
        "hospitalization",
        "life-threatening",
        "disability",
        "death",
    ],
    "reporting_timeline": [
        "15 calendar days",
        "90 days",
        "within 15",
        "within 90",
    ],
    "expectedness": [
        "package insert",
        "prescribing information",
        "product information",
    ],
}


def normalize_text(value):
    """Normalize text for simple keyword comparisons."""

    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().split())


def verify_claim_support(claim, passage):
    """
    Perform a basic deterministic keyword check.

    A positive result means relevant terminology appears in
    the passage. It does NOT prove semantic entailment.
    """

    claim_text = normalize_text(claim)
    passage_text = normalize_text(passage)

    if not claim_text or not passage_text:
        return False

    matched_keywords = []

    for category, keywords in CLAIM_KEYWORDS.items():

        if any(keyword in claim_text for keyword in keywords):

            if any(
                keyword in passage_text
                for keyword in keywords
            ):
                matched_keywords.extend(
                    keyword
                    for keyword in keywords
                    if keyword in passage_text
                )

    # Generic fallback: require meaningful claim terms to overlap.
    if not matched_keywords:

        ignored_words = {
            "the", "is", "a", "an", "of", "to",
            "and", "for", "in", "on", "by", "with",
            "this", "that", "from", "as",
        }

        claim_terms = {
            word for word in claim_text.split()
            if len(word) > 3 and word not in ignored_words
        }

        passage_terms = set(passage_text.split())

        overlap = claim_terms.intersection(passage_terms)

        return len(overlap) >= 2

    return True


def verify_citations(assessment, evidence):
    """Verify that every citation resolves to retrieved evidence."""

    evidence_by_chunk = {
        item.get("chunk_id"): item
        for item in evidence
        if item.get("chunk_id")
    }

    verified_evidence = []
    reasons = []

    citations = assessment.get("evidence_references", [])

    if not citations:
        reasons.append(
            "The assessment contains no evidence references."
        )

    for citation in citations:

        if not isinstance(citation, dict):
            reasons.append(
                "An evidence reference has an invalid format."
            )
            continue

        chunk_id = citation.get("chunk_id")
        claim = citation.get("claim", "")

        retrieved = evidence_by_chunk.get(chunk_id)

        if not retrieved:
            reasons.append(
                f"Citation {chunk_id} does not match retrieved evidence."
            )
            continue

        required_metadata = [
            retrieved.get("document_id"),
            retrieved.get("document_name"),
            retrieved.get("pdf_page"),
            retrieved.get("passage"),
        ]

        if not all(required_metadata):
            reasons.append(
                f"Citation {chunk_id} has incomplete source metadata."
            )
            continue

        if not claim:
            reasons.append(
                f"Citation {chunk_id} has no associated claim."
            )
            continue

        if not verify_claim_support(
            claim,
            retrieved["passage"],
        ):
            reasons.append(
                f"Citation {chunk_id} does not pass the keyword "
                "support check for its claim."
            )
            continue

        verified_evidence.append(retrieved)

    return verified_evidence, reasons


def verify_reporting_scope(case, evidence):
    """Check whether evidence scope matches reporting context."""

    reasons = []

    reporting_context = case.get(
        "reporting_context",
        "marketed_product",
    )

    if reporting_context == "marketed_product":

        for item in evidence:

            if item.get("scope") == "clinical_trial":
                reasons.append(
                    "Clinical-trial provisions cannot establish "
                    "marketed-product reporting obligations."
                )

        if not any(
            item.get("scope") in ALLOWED_MARKETED_PRODUCT_SCOPES
            for item in evidence
        ):
            reasons.append(
                "No marketed-product guidance was verified."
            )

    return reasons


def verify_expectedness(assessment, evidence):
    """
    Expectedness must be based on an approved drug-specific
    package insert, not general pharmacovigilance guidance.
    """

    reasons = []

    expectedness = assessment.get("expectedness")

    package_insert_available = any(
        item.get("scope") == "package_insert"
        for item in evidence
    )

    if expectedness in {"expected", "unexpected"}:
        if not package_insert_available:
            reasons.append(
                "Expectedness was classified without an approved "
                "drug-specific package insert."
            )

    if expectedness == "undetermined":
        reasons.append(
            "Expectedness remains undetermined because an approved "
            "package insert is unavailable."
        )

    return reasons


def verify_seriousness(assessment, case, evidence):
    """Check seriousness against available case facts."""

    reasons = []

    seriousness = assessment.get("seriousness")

    if seriousness == "serious":

        if case.get("hospitalized") is True:

            if case.get("hospitalization_due_to_event") is not True:
                reasons.append(
                    "Hospitalisation is recorded, but its relationship "
                    "to the adverse event has not been confirmed."
                )

    elif seriousness == "undetermined":
        reasons.append(
            "Seriousness could not be established from the available "
            "case information."
        )

    return reasons


def verify_reporting_timeline(assessment, evidence):
    """
    Verify that a proposed reporting timeline has matching
    marketed-product guidance.
    """

    reasons = []

    route = assessment.get("reporting_route", "")
    timeline = assessment.get("reporting_timeline", "")

    if not route and not timeline:
        return reasons

    combined = normalize_text(f"{route} {timeline}")

    if "15" in combined:
        matching_evidence = any(
            item.get("scope") == "marketed_product"
            and (
                "15 calendar days" in normalize_text(item.get("passage", ""))
                or "within 15" in normalize_text(item.get("passage", ""))
            )
            for item in evidence
        )

        if not matching_evidence:
            reasons.append(
                "The 15-day reporting timeline could not be verified "
                "against retrieved marketed-product guidance."
            )

    if "90" in combined:
        matching_evidence = any(
            item.get("scope") == "marketed_product"
            and (
                "90 days" in normalize_text(item.get("passage", ""))
                or "within 90" in normalize_text(item.get("passage", ""))
            )
            for item in evidence
        )

        if not matching_evidence:
            reasons.append(
                "The 90-day reporting timeline could not be verified "
                "against retrieved marketed-product guidance."
            )

    return reasons


def evidence_verification_agent(
    state: PharmacovigilanceState,
) -> dict:
    """
    Evidence Verification Agent.

    Responsibilities:
    1. Resolve citations against retrieved passages.
    2. Check basic claim-to-passage keyword support.
    3. Validate regulatory source scope.
    4. Check expectedness and seriousness limitations.
    5. Escalate unsupported or uncertain assessments.
    """

    assessment = state.get("clinical_assessment", {})
    evidence = state.get("clinical_evidence", [])
    case = state.get("case_data", {})

    verified_evidence, reasons = verify_citations(
        assessment,
        evidence,
    )

    reasons.extend(
        verify_reporting_scope(case, verified_evidence)
    )

    reasons.extend(
        verify_expectedness(assessment, verified_evidence)
    )

    reasons.extend(
        verify_seriousness(
            assessment,
            case,
            verified_evidence,
        )
    )

    reasons.extend(
        verify_reporting_timeline(
            assessment,
            verified_evidence,
        )
    )

    reasons = list(dict.fromkeys(reasons))

    verification_passed = len(reasons) == 0

    return {
        "verified_evidence": verified_evidence,
        "verification_result": {
            "passed": verification_passed,
            "valid_citation_count": len(verified_evidence),
            "reasons": reasons,
        },
        "escalation_required": not verification_passed,
        "escalation_reasons": reasons,
        "current_agent": "evidence_verification",
    }
