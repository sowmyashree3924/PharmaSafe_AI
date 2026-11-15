# PharmaSafe AI - Evidence Index

## Project

Pharmacovigilance Adverse Event Intake and Triage Service

## Purpose

This index identifies the reference documents and evidence notes prepared for the academic prototype. The system must retrieve supporting evidence and present it for qualified human review. It must not make final medical or regulatory decisions.

## 1\. Indian Pharmacopoeia Commission (IPC) Guidance

Source:
Pharmacovigilance Guidance Document for Marketing Authorisation Holders of Pharmaceutical Products

Publisher:
Indian Pharmacopoeia Commission and CDSCO

Version:
2.0 (2024)

Local PDF:
corpus/guidance/Pharmacovigilance Guidance for Marketing Authorization Holders.pdf

Extracted text:
docs/planning/extracted\_text/Pharmacovigilance Guidance for Marketing Authorization Holders.txt

Evidence notes:
docs/planning/ipc\_evidence\_notes.txt

Important evidence:

* Section 2.5.3.6: seriousness criteria, including hospitalisation.
* Section 2.7.1: serious adverse event reporting provisions for marketing authorisation holders.
* Section 2.7.2: non-serious adverse event reporting provisions.
* Section 2.8: causality assessment and reference to WHO-UMC.

Scope:
These are marketing authorisation holder reporting provisions. They must not be confused with clinical-trial reporting requirements.

## 2\. New Drugs and Clinical Trials Rules, 2019

Publisher:
Central Drugs Standard Control Organization (CDSCO), Government of India

Local PDF:
corpus/regulations/New Drugs and Clinical Trials Rules, 2019.pdf

Extracted text:
docs/planning/extracted\_text/New Drugs and Clinical Trials Rules, 2019.txt

Evidence notes:
docs/planning/rules\_evidence\_notes.txt

Important evidence:

* Section 2(ff): definition of serious adverse event in the relevant study context.
* Ethics Committee responsibilities.
* Rule 42: serious adverse event reporting provisions in clinical trials and related studies.

Scope:
These provisions concern clinical trials, bioavailability studies and bioequivalence studies. Do not apply their timelines automatically to general post-marketing reports involving marketed products.

Note:

Page references reviewed against the source PDF. See the evidence notes for the checked page ranges.

## 3\. WHO-UMC Causality Assessment

Source:
The Use of the WHO-UMC System for Standardised Case Causality Assessment

Publisher:
WHO Collaborating Centre for International Drug Monitoring (UMC)

Publication date:
Not verified.

Local PDF:
corpus/additional\_references/WHO-UMC\_Causality\_Assessment.pdf

Extracted text:
docs/planning/extracted\_text/WHO-UMC\_Causality\_Assessment.txt

Evidence notes:
docs/planning/who\_umc\_evidence\_notes.txt

Important evidence:

* PDF page 1: purpose and limitations of causality assessment.
* PDF page 2: six causality categories and their criteria.
* PDF page 3: distinctions between probable and possible.

Categories:

1. Certain
2. Probable / Likely
3. Possible
4. Unlikely
5. Conditional / Unclassified
6. Unassessable / Unclassifiable

Scope:
These categories support structured assessment. They do not prove that a drug caused an event.

## 4\. Approved Marketed Drug Package Insert

Status:
Pending guide/team selection of the drug.

Expected location:
corpus/package\_insert/

Expected extracted text location:
docs/planning/extracted\_text/

Evidence required after selection:

* Approved product and manufacturer identification.
* Listed adverse reactions.
* Relevant warnings and precautions.
* Source page references for expectedness checking.

Do not invent a drug, adverse reaction listing or package-insert evidence.

## Implementation requirements

* Every evidence-based output should include a source document and page or section reference.
* Expectedness must be checked against the selected approved package insert.
* Seriousness and expectedness are separate assessments.
* Missing or contradictory information must be flagged.
* Uncertain cases must be escalated for qualified human review.
* The prototype must not submit regulatory reports or make final regulatory decisions.
* Use synthetic reports only; do not use real patient information.

## Prepared files

* docs/planning/corpus\_manifest.csv
* docs/planning/ipc\_evidence\_notes.txt
* docs/planning/rules\_evidence\_notes.txt
* docs/planning/who\_umc\_evidence\_notes.txt
* docs/planning/extracted\_text/

