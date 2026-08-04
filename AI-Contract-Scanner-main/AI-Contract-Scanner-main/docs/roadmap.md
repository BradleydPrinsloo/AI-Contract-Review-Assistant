# Roadmap

This roadmap separates verified work from planned public-portfolio improvements.

## Completed and verified

- Versioned portable Windows release bundles
- Required-input validation before packaging
- Client launcher and quick-start generation
- Safe sample-contract delivery
- Release manifest generation
- Per-file SHA-256 checksum manifest
- Final ZIP checksum generation
- Signed and unsigned release notes

## Portfolio preparation

- [x] Professional README
- [x] Architecture overview for the release workflow
- [x] Installation and user documentation
- [x] Security and contribution policies
- [x] Repository ignore rules
- [ ] Review complete source tree for secrets and client information
- [ ] Publish sanitized application source
- [ ] Publish verified dependency files
- [ ] Add sanitized application screenshots
- [ ] Add safe sample contracts
- [ ] Add automated tests
- [ ] Add continuous-integration checks

## Product documentation

- [ ] Document contract ingestion and parsing
- [ ] Document the risk-detection engine
- [ ] Document scoring and finding prioritization
- [ ] Document report generation and exports
- [ ] Document local history and data retention
- [ ] Add troubleshooting guide

## Engineering improvements

The following are candidates pending review of the full codebase:

- Reproducible developer setup
- Static analysis and formatting checks
- Unit and integration test coverage
- Automated release validation
- Release signing when a code-signing certificate is available
- Dependency and vulnerability scanning
- Improved error reporting and structured logging

## Future product direction

Future capabilities should only be listed as committed features after requirements and implementation are verified. Potential areas include improved review workflows, configurable organization-specific rules, richer reporting, and optional assisted analysis with appropriate privacy controls.
