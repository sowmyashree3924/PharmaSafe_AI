# PharmaSafe AI - Member 1 Handover

## Role
Member 1 - Official Reference Documents and Corpus Preparation

## Handover purpose
Provide the prepared reference documents, extracted text and evidence notes to the team member implementing retrieval and evidence verification.

## 1. Reference documents prepared

| Document | Local location | Status |
|---|---|---|
| New Drugs and Clinical Trials Rules, 2019 | corpus/regulations/ | Downloaded and extracted |
| IPC Pharmacovigilance Guidance, Version 2.0 (2024) | corpus/guidance/ | Downloaded and extracted |
| WHO-UMC Causality Assessment | corpus/additional_references/ | Downloaded and extracted |
| Approved marketed drug package insert | corpus/package_insert/ | Pending drug selection |

## 2. Extracted text

All three available reference PDFs have extracted text files in:

docs/planning/extracted_text/

Extraction script:

scripts/extract_corpus.py

The extraction was completed successfully using pypdf.

## 3. Evidence notes prepared

1. IPC evidence:
   docs/planning/ipc_evidence_notes.txt

2. New Drugs and Clinical Trials Rules evidence:
   docs/planning/rules_evidence_notes.txt

3. WHO-UMC causality evidence:
   docs/planning/who_umc_evidence_notes.txt

4. Combined evidence index:
   docs/planning/evidence_index.md

## 4. Corpus manifest

File:
docs/planning/corpus_manifest.csv

The manifest records document identifiers, publishers, versions, local paths, extraction status and review status.

## 5. Important instructions for Member 2

- Use the extracted text as the starting point for preparing the retrieval corpus.
- Preserve the source document identity and PDF page references.
- Keep the IPC marketing authorisation holder reporting provisions separate from clinical-trial provisions in the New Drugs and Clinical Trials Rules.
- Use WHO-UMC categories as structured reference criteria, not proof of causation.
- Do not implement expectedness checking until the selected approved package insert is available.
- Retrieval results should return the source document, relevant section or page, and supporting passage.
- If evidence is missing, contradictory or insufficient, flag the case for qualified human review.
- Use only synthetic adverse-event reports for development and testing.

## 6. Pending work

The approved marketed drug package insert has not been added because the guide/team has not yet confirmed which drug to use.

After the team selects the drug:

1. Obtain the appropriate approved package insert from an authoritative source.
2. Save the PDF in corpus/package_insert/.
3. Extract its text into docs/planning/extracted_text/.
4. Record its publisher, product, version/date and source in corpus_manifest.csv.
5. Prepare evidence notes for listed adverse reactions and relevant warnings.
6. Share the updated corpus with Member 2.

## 7. Safety and scope

PharmaSafe AI is an academic decision-support prototype.

It must:
- Provide traceable evidence.
- Identify missing information.
- Separate seriousness from expectedness.
- Escalate uncertain cases to qualified human review.

It must not:
- Diagnose patients.
- Claim to prove drug causation.
- Submit regulatory reports.
- Make final medical or regulatory decisions.

## Handover status

Three reference documents downloaded and extracted.
Three evidence-note files prepared.
Evidence index prepared.
Package insert pending guide/team drug selection.
Final evidence page-reference audit completed. Rules definition 2(ff) was checked against PDF pages 6-7, Rule 42 provisions against PDF pages 39-42, and IPC and WHO-UMC page references were reviewed.

