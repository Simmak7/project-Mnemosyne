# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.0-beta | Yes |
| < 1.1.0 | No |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Mnemosyne, please report it responsibly.

### How to Report

1. **GitHub Private Advisory** (preferred): Use [GitHub Security Advisories](https://github.com/Simmak7/project-Mnemosyne/security/advisories/new) to report the vulnerability privately.

2. **Email**: Send details to the repository owner via their GitHub profile contact information.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

- **Acknowledgment** within 48 hours
- **Initial assessment** within 1 week
- **Fix or mitigation** as soon as practically possible, depending on severity
- **Credit** in the changelog and release notes (unless you prefer anonymity)

## Responsible Disclosure

We ask that you:

- **Do not** publicly disclose the vulnerability before a fix is available
- **Do not** exploit the vulnerability beyond what is necessary to demonstrate it
- **Do** provide sufficient detail for us to reproduce and fix the issue

## Scope

This policy covers the Mnemosyne application code in this repository. Third-party dependencies (Ollama, PostgreSQL, Redis, etc.) should be reported to their respective maintainers.

## Security Best Practices for Users

Since Mnemosyne runs locally, your security posture depends on your environment:

- Keep Docker and all containers updated
- Use strong passwords for your Mnemosyne account
- Enable two-factor authentication (TOTP) in Settings
- Do not expose ports 3000/8000 to the public internet without proper authentication
- Regularly back up your PostgreSQL data volume
