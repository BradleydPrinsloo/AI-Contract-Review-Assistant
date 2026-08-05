# User Guide

## Purpose

ContractIQ is designed to assist a user with reviewing contract language, organizing findings, and producing a clear report for human evaluation.

It is a support tool. It does not provide legal advice and should not be treated as a substitute for review by a qualified professional.

## Basic workflow

1. Launch the application with `START-HERE.cmd` or `python main.py` during development.
2. Select **Open Contract**.
3. Choose a contract that you are authorized to review.
4. Select **Scan Contract**.
5. Review the displayed risk score, findings, summary, and any Clause Library guidance attached to each finding.
6. Use **Repository** to search saved reviews by vendor, client, reviewer, risk, status, tag, department, or version.
7. Use **Clause Library** to maintain organization-approved clause wording, rejected wording, examples, risk levels, and explanation notes.
8. Use **About** to confirm the ContractIQ version and decision-support notice.

## Clause Library workflow

The Clause Library stores organization-specific wording standards separately from scanned contract history.

1. Open **Clause Library** from the platform sidebar.
2. Select **New Clause**.
3. Enter a clause name, category, risk level, company wording, rejected wording, examples, and optional explanation notes.
4. Select **Save Clause** to store the clause standard locally.
5. Use search, risk, and status filters to find active or archived clauses.
6. Select **Archive Clause** when a standard should no longer be used, while preserving its audit history.

Explanation notes are provider-abstracted. If no AI provider adapter is configured, ContractIQ stores deterministic local notes instead of calling a hardcoded AI service.

When a scanned finding matches an active Clause Library standard, the finding detail panel and full reports include the standard name, approved wording, rejected wording, examples, and explanation notes. Use this as review guidance only; the reviewer must still confirm the actual contract language and surrounding context.

## Using your own document

ContractIQ supports PDF, DOCX, and TXT contracts.

Before opening a document:

- Confirm that you are authorized to process it.
- Avoid using confidential documents in demonstrations or public environments.
- Confirm where exported results and local scan history will be stored.
- Review all findings manually before relying on them.

## Interpreting findings

A detected phrase is not automatically a legal problem. Context matters. Users should evaluate:

- The complete clause, not only the matched words
- Definitions elsewhere in the contract
- Exceptions and limitations
- Which party the obligation applies to
- Governing law and project-specific requirements
- Whether the finding is a false positive

## Recommended workflow

1. Open the contract.
2. Run the scan.
3. Review high-priority findings first.
4. Compare matched findings against any Clause Library approved/rejected wording.
5. Read the surrounding clause text.
6. Mark false positives or items requiring escalation.
7. Export or record the review results.
8. Escalate legal interpretation to a qualified reviewer.

## Data handling

Do not upload client contracts, exported findings, private databases, or screenshots containing confidential text to this public repository.

## Documentation still pending

Detailed screen-by-screen instructions and screenshots will be added after the user interface has been reviewed and all images have been sanitized.
