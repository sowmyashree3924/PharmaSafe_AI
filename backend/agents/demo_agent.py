"""Local evidence-first demo path; intentionally needs no model key or network."""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _citation(ref: str, document: str, section: str, page: str, passage: str, url: str = "", local_source: str = "") -> dict:
    return {
        "evidence_id": ref,
        "document": document,
        "section": section,
        "page": page,
        "passage": passage,
        "source_url": url,
        "local_source": local_source,
    }


async def run_demo_assessment(case: dict) -> dict:
    """Run bounded local tools and a separate evidence verification hand-off."""
    started = time.perf_counter()
    trace = []
    evidence = []

    def step(name: str, fn):
        t0 = time.perf_counter()
        value = fn()
        trace.append({"step": name, "latency_ms": round((time.perf_counter() - t0) * 1000, 2)})
        return value

    # Agent 1: intake checks and case-field extraction.
    case_fields = step("intake_agent.case_lookup", lambda: {
        "drug": case["drug_name"].strip(),
        "reaction": case["reaction_description"].strip(),
        "days_to_onset": (datetime.fromisoformat(case["onset_date"].replace("Z", "+00:00"))
                          - datetime.fromisoformat(case["drug_start_date"].replace("Z", "+00:00"))).days,
        "outcome": case["outcome"],
    })

    def search_label():
        text = (ROOT / "docs/planning/lamotrigine_label_excerpt.md").read_text(encoding="utf-8")
        label_sections = {}
        for line in text.splitlines():
            match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line)
            if match:
                label_sections[match.group(1)] = match.group(2)
        is_lamotrigine = "lamotrigine" in case_fields["drug"].lower()
        skin_match = bool(re.search(r"peel|skin|rash|blister", case_fields["reaction"], re.I))
        if is_lamotrigine and skin_match:
            passages = [
                ("LABEL-BOXED-WARNING", "Boxed Warning — Serious Skin Rashes (paraphrase)"),
                ("LABEL-MED-GUIDE-SKIN", "Medication Guide — serious skin reactions (paraphrase)"),
                ("LABEL-MED-GUIDE-TIMING", "Medication Guide — timing (paraphrase)"),
            ]
            for ref, section in passages:
                passage = label_sections.get(section, "")
                if not passage:
                    continue
                evidence.append(_citation(ref, "DailyMed lamotrigine tablets label (U.S.)", section,
                    "section reference", passage,
                    "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6139a858-700c-4eb9-9f84-99d280bde326",
                    "docs/planning/lamotrigine_label_excerpt.md"))
        return {"label_match": bool(evidence), "label_in_scope": False, "excerpt_loaded": bool(text)}

    label_result = step("evidence_agent.corpus_search", search_label)

    def lookup_ipc():
        notes = (ROOT / "docs/planning/ipc_evidence_notes.txt").read_text(encoding="utf-8")
        cite = _citation("IPC-2.5.3.6-P31", "IPC Pharmacovigilance Guidance for Marketing Authorisation Holders, v2.0 (2024)",
            "Section 2.5.3.6", "PDF p. 31 (printed p. 20)",
            "Hospitalisation or prolongation of existing hospitalisation is included as a seriousness criterion.",
            local_source="docs/planning/ipc_evidence_notes.txt")
        route_cite = _citation("IPC-2.7.1-P33", "IPC Pharmacovigilance Guidance for Marketing Authorisation Holders, v2.0 (2024)",
            "Section 2.7.1", "PDF p. 33 (printed p. 22)",
            "The guidance states that MAHs must report serious adverse events within 15 calendar days of receiving information.",
            local_source="docs/planning/ipc_evidence_notes.txt")
        if "15 calendar days" in notes and "hospitalisation" in notes.lower():
            evidence.extend([cite, route_cite])
            return True
        return False

    ipc_found = step("evidence_agent.clause_lookup", lookup_ipc)

    serious = case_fields["outcome"] in {"fatal", "hospitalisation", "disability", "congenital_anomaly"}
    seven_day = case_fields["days_to_onset"] == 7
    drug_supported = label_result["label_match"]
    country_label_gap = drug_supported and not label_result["label_in_scope"]
    injection_attempt = bool(re.search(
        r"ignore (all |previous )?instructions|system prompt|reveal .*prompt|call .*tool|override (the )?(system|developer)",
        case_fields["reaction"], re.I,
    ))
    reasons = []
    if not drug_supported:
        reasons.append("No matching approved product label is available for this drug and reaction in the demo corpus.")
    if country_label_gap:
        reasons.append("The matching source is a U.S. label; verify expectedness against the applicable India-approved product information.")
    if not seven_day:
        reasons.append("Review the event timeline and source-label timing with a qualified reviewer.")
    if not ipc_found:
        reasons.append("IPC seriousness or reporting evidence was unavailable.")
    if injection_attempt:
        reasons.append("Free-text instruction-like content was detected and excluded from assessment; qualified review is required.")

    # Agent 2: assessment and verification hand-off. Only evidence returned by the local tools is cited.
    assessment = {
        "seriousness": "serious" if serious else "not established as serious",
        "expectedness": "listed in the U.S. reference label" if drug_supported else "undetermined",
        "causality": "not assessed; timing alone cannot establish causation",
        "reasoning": "Reported hospitalisation meets the cited seriousness criterion. Skin peeling matches the lamotrigine label's serious-skin-reaction warning; this does not diagnose a condition or prove drug causality.",
    }
    if drug_supported and case_fields["days_to_onset"] == 7:
        assessment["reasoning"] += " The one-week onset is earlier than the label's more-likely 2–8 week period, though the label says serious rash can happen at any time."

    verification_start = time.perf_counter()
    evidence_ids = {item["evidence_id"] for item in evidence}
    def citation_resolves(item):
        source_path = item.get("local_source", "")
        if not source_path or item["evidence_id"] not in evidence_ids:
            return False
        source_text = " ".join((ROOT / source_path).read_text(encoding="utf-8").casefold().split())
        passage = " ".join(item.get("passage", "").casefold().split())
        return bool(passage and passage in source_text)
    verification_passed = bool(evidence) and all(citation_resolves(item) for item in evidence)
    trace.append({"step": "verification_agent.citation_check", "latency_ms": round((time.perf_counter() - verification_start) * 1000, 2)})
    if not verification_passed:
        reasons.append("Citation verification did not pass; escalation is required.")

    route_possible = serious and ipc_found and verification_passed
    route = "expedited_reporting_review" if route_possible else "human_review"
    timeline = "Review against the 15-calendar-day serious-event provision" if route_possible else "Not determined"
    if route_possible:
        reasons.append("Expedited reporting review is suggested from seriousness; a qualified person must confirm applicability and submit any report.")

    elapsed = round((time.perf_counter() - started) * 1000, 2)
    return {
        "decision_status": "human_review_required" if reasons else "completed",
        "routing_recommendation": route,
        "reporting_route": route,
        "reporting_timeline": timeline,
        "seriousness": {"value": assessment["seriousness"], "reason": "Hospitalisation is a seriousness criterion." if serious else "No reported seriousness criterion was identified."},
        "expectedness": {"value": assessment["expectedness"], "reason": "The source is a U.S. label and is not verified as the applicable local insert." if country_label_gap else "No matching label evidence was found."},
        "clinical_assessment": assessment,
        "verification": {"passed": verification_passed, "valid_citation_count": len(evidence), "reasons": [] if verification_passed else ["Citation could not be resolved to retrieved evidence."]},
        "citations": evidence,
        "retrieved_evidence": evidence,
        "escalation_required": bool(reasons),
        "escalation_reason": " ".join(reasons),
        "trace": {"correlation_id": case.get("_correlation_id", ""), "agent_handoff": ["intake_agent", "evidence_agent", "verification_agent", "regulatory_router"], "steps": trace, "tool_calls": 3, "prompt_version": "local-demo-v1", "guardrail": "instruction_like_text_flagged" if injection_attempt else "clear", "latency_ms": elapsed, "estimated_cost_usd": 0},
        "disclaimer": "Academic decision support using synthetic reports only. Not a diagnosis or regulatory determination. A qualified pharmacovigilance professional must make the final decision.",
    }
