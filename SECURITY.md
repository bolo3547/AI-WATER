# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in AquaWatch NRW, please report it responsibly:

1. **Do NOT open a public issue** for security vulnerabilities
2. Email security details to: **engineering@aquawatch.io**
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 5 business days
- **Fix release**: Depends on severity (critical: within 7 days)

## Security Best Practices

When deploying AquaWatch NRW:

- **Never** commit `.env` files or credentials to version control
- Rotate `SECRET_KEY`, `JWT_SECRET`, and database passwords regularly
- Use environment variables for all sensitive configuration
- Enable HTTPS/TLS for all production endpoints
- Review the `.env.example` file for required security configurations
- Keep all dependencies updated to their latest secure versions
