# ContractIQ Contract Intelligence Platform Roadmap

## Objective

Evolve ContractIQ from a desktop analysis application into a modular contract-intelligence platform that can be sold as a complete software asset, licensed as white-label technology, or acquired by a legal-tech, construction-tech, procurement, document-management, or Microsoft solutions company.

The platform must remain demonstrable as a standalone Windows product while its business logic is separated into reusable services that a buyer can integrate into a web application, API, Word add-in, or existing enterprise platform.

## Product modules

### 1. Contract Scanner

Current foundation:

- PDF, DOCX, and TXT extraction
- OCR fallback
- Configurable deterministic rules
- Context-aware false-positive suppression
- Risk scoring
- Executive summaries
- Review repository
- DOCX, CSV, and TXT exports

Required hardening:

- Structured logging
- Error telemetry that does not expose contract text
- Reproducible Windows builds
- Automated tests
- Performance benchmarks
- Review-state persistence

### 2. Clause Intelligence

- Clause segmentation
- Clause classification independent of exact keywords
- Standard clause taxonomy
- Confidence and explanation metadata
- Missing-clause detection
- Protective, neutral, and adverse clause identification
- Contract-type profiles

Initial profiles:

- General commercial
- Construction and subcontracting
- Vendor and supplier
- Services and consulting
- Employment
- NDA and confidentiality
- Software licensing
- Procurement
- Lease

### 3. Contract Comparison

- Compare two contract versions
- Identify added, removed, and modified clauses
- Compare against an approved template
- Compare against a prior negotiated agreement
- Risk-delta summary
- Side-by-side clause viewer
- Export comparison report

### 4. Review Playbooks and Policy Engine

- Organization-defined preferred language
- Required clauses
- Prohibited terms
- Acceptable fallback positions
- Risk thresholds
- Approval requirements
- Industry-specific playbooks
- Policy-compliance report

### 5. AI Review Assistant

AI must remain optional and visibly separated from deterministic findings.

- Plain-English clause explanations
- Obligation summaries
- Negotiation questions
- Suggested fallback wording
- Suggested clause rewrites
- Executive summary generation
- Missing-clause suggestions
- Evidence links back to exact source text

### 6. Redline and Drafting Assistant

- Accept/reject suggested revisions
- Generate proposed replacement language
- Export redlined DOCX
- Maintain change history
- Reviewer notes
- Original-versus-proposed comparison

### 7. Review Workflow

- Review status
- Reviewer assignment
- Comments and notes
- Approval stages
- Escalation rules
- Audit trail
- Exportable review record

The first implementation can remain single-user and local. Multi-user collaboration should be implemented behind service interfaces so a buyer can connect its own identity, database, and hosting stack.

### 8. Integration Layer

- Python service API around document extraction, scanning, scoring, comparison, and reporting
- Stable JSON schemas
- Command-line interface
- Microsoft Word add-in integration path
- SharePoint and OneDrive integration path
- Webhook and REST integration documentation
- Import/export adapters for third-party CLM systems

## Target architecture

```text
Desktop UI / Word Add-in / Web UI / Buyer Platform
                         |
                         v
                 Application Services
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
   Document Service  Analysis Engine  Review Workflow
          |              |              |
          +--------------+--------------+
                         |
                         v
       Repository / Playbooks / Audit / Reports
                         |
                         v
              Optional AI Provider Layer
```

## Engineering principles for acquisition readiness

- No client data, credentials, or proprietary datasets in source control
- Core analysis logic independent from the PySide6 user interface
- Provider-agnostic AI interface
- Stable data models and versioned schemas
- Automated unit and integration tests
- Reproducible builds
- Dependency and license inventory
- Security documentation
- Clear ownership of all source code and assets
- Buyer-ready architecture, deployment, and handoff documentation

## Build phases

### Phase A — Product hardening

- Refactor core analysis out of UI orchestration
- Add test fixtures and unit tests
- Add structured logging
- Add configuration model
- Add PyInstaller specification
- Add GitHub Actions validation
- Add installer and release process

Exit criteria:

- Existing desktop features remain functional
- Automated tests cover scanner, scoring, repository, and exports
- A clean Windows build can be reproduced from documented steps

### Phase B — Contract profiles and clause taxonomy

- Add contract profile selector
- Define standard clause taxonomy
- Create separate rule libraries per profile
- Add missing-clause detection
- Add profile-specific recommendations

Exit criteria:

- The same document can be analyzed under different profiles
- Findings identify both detected and expected-but-missing clauses

### Phase C — Comparison engine

- Implement clause segmentation
- Implement clause similarity matching
- Compare contract versions and templates
- Add risk-delta scoring
- Add comparison dashboard and exports

Exit criteria:

- Users can compare two contracts and identify material changes

### Phase D — Playbook and compliance engine

- Define playbook schema
- Add preferred, fallback, prohibited, and required language
- Evaluate contracts against selected playbooks
- Add compliance dashboard and report

Exit criteria:

- A company can encode review policy without changing application code

### Phase E — AI assistant and redlining

- Add provider interface
- Add evidence-grounded explanations
- Add negotiation and rewrite suggestions
- Add redline proposal workflow
- Add DOCX redline export

Exit criteria:

- AI outputs cite the exact clause text used
- Deterministic findings remain available without AI

### Phase F — Buyer integration package

- Publish service API
- Add CLI
- Add integration examples
- Add Word add-in proof of concept
- Add deployment and white-label documentation
- Produce buyer due-diligence package

Exit criteria:

- A third party can integrate the analysis engine without using the desktop UI

## Buyer-ready deliverables

- Source repository with documented ownership
- Windows installer and portable build
- Architecture documentation
- API and schema documentation
- Automated test results
- Security and privacy documentation
- Dependency and third-party license report
- Product demo video
- Benchmark report
- Feature matrix
- Sample rule profiles and playbooks using synthetic data
- Buyer handoff guide
- White-label guide
- Intellectual-property schedule

## Recommended commercial positioning

ContractIQ Contract Intelligence Platform is a privacy-conscious contract review and comparison engine combining deterministic policy checks with optional AI assistance. It can operate as a standalone Windows application or be integrated into an existing legal-tech, construction-tech, procurement, document-management, or Microsoft 365 platform.

## Immediate development priority

Start with Phase A. Product hardening creates the foundation required for every later module and reduces technical risk for a future buyer.