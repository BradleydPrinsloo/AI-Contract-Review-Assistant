# User Guide

## Purpose

The Construction Contract Risk Scanner is designed to assist a user with reviewing contract language and organizing findings for human evaluation.

It is a support tool. It does not provide legal advice and should not be treated as a substitute for review by a qualified professional.

## Quick demonstration

The verified portable release includes safe text fixtures for demonstration and release testing.

1. Launch the application with `START-HERE.cmd`.
2. Select **Open Contract**.
3. Choose one of the files under `sample_contracts/`:
   - `01-high-risk-demo.txt`
   - `02-mixed-context-demo.txt`
   - `03-subtle-real-clause-demo.txt`
4. Select **Scan Contract**.
5. Review the displayed risk score, findings, and summary.

## Using your own document

The verified quick-start documentation indicates support for PDF, DOCX, and TXT contracts.

Before opening a document:

- Confirm that you are authorized to process it.
- Avoid using confidential documents in demonstration or public environments.
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
4. Read the surrounding clause text.
5. Mark false positives or items requiring escalation.
6. Export or record the review results.
7. Escalate legal interpretation to a qualified reviewer.

## Data handling

Do not upload client contracts, exported findings, private databases, or screenshots containing confidential text to this public repository.

## Documentation still pending

Detailed screen-by-screen instructions and screenshots will be added after the user interface has been reviewed and all images have been sanitized.
