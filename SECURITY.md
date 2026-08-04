# Security Policy

## Supported versions

The public repository does not yet publish supported application versions. Support information will be added after the source and release history have completed a security review.

## Reporting a vulnerability

Do not disclose security vulnerabilities, credentials, client contracts, personal information, proprietary rule sets, or other sensitive material in a public GitHub issue.

Contact the project owner privately through the contact method listed on the associated GitHub profile. Include:

- A concise description of the issue
- The affected component and version
- Safe reproduction steps
- Potential impact
- Suggested remediation, if known

## Repository security rules

The following must never be committed:

- Real client contracts or customer records
- API keys, passwords, access tokens, or private certificates
- Firebase or cloud service-account files
- `.env` files
- Proprietary client databases or risk-rule libraries
- Generated exports containing contract text
- Unsanitized screenshots
- Build artifacts or release bundles intended for private delivery

## Legal and professional-use notice

The application assists human review and does not provide legal advice. Security reports should focus on software behavior, data exposure, packaging integrity, or deployment risk rather than the legal meaning of contract findings.
