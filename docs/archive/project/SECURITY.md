# Security Policy

## Supported Versions

During the beta phase, only the latest beta release is supported for security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.0-beta | :white_check_mark: |
| < 1.0.0-beta | :x:                |

## Reporting a Vulnerability

We take the security of the Elson Wealth Trading Platform seriously. We appreciate your efforts to responsibly disclose your findings, and we will make every effort to acknowledge your contributions.

### How to Report a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them directly to our security team by emailing **security@elsonwealth.com**. If possible, encrypt your message using our PGP key.

Please include the following information in your report:

- Type of vulnerability
- Full path of the affected file(s)
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### Response Timeline

- We aim to acknowledge receipt of your vulnerability report within 24 hours.
- We will provide an initial assessment of the report within 3 business days.
- We will keep you informed about our progress throughout the process.
- Once the vulnerability is confirmed and fixed, we will recognize your contribution (unless you prefer to remain anonymous).

## Responsible Disclosure Guidelines

- Provide us reasonable time to address the vulnerability before any public disclosure.
- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our services.
- Only interact with accounts you own or with explicit permission from the account holder.
- Do not engage in extortion or any threatening behavior.

## Security Measures in the Beta Phase

During the beta phase, we have implemented the following security measures:

1. **Restricted Trading:** All trading is paper-based with no real money transactions.
2. **Isolated Environment:** The beta environment is isolated from production systems.
3. **Limited Data:** User data is minimized and does not include sensitive financial information.
4. **Regular Security Scanning:** Automated and manual security testing is performed.
5. **Authentication:** Two-factor authentication is available and encouraged for beta testers.

## Security Best Practices for Beta Testers

1. Use a strong, unique password for your Elson Wealth Trading Platform account.
2. Enable two-factor authentication when available.
3. Do not share your beta access credentials with others.
4. Be cautious of phishing attempts - we will never ask for your password via email.
5. Report any suspicious behavior or potential security issues promptly.

## Security Features

The Elson Wealth Trading Platform includes several security features:

- **JWT Authentication:** Secure token-based authentication with short expiration times.
- **TLS Encryption:** All API communications are encrypted using TLS 1.3.
- **Role-Based Access Control:** Granular permissions based on user roles.
- **Rate Limiting:** Protection against brute force and DoS attacks.
- **Input Validation:** Thorough validation of all input data.
- **Audit Logging:** Comprehensive logging of security-relevant events.

Thank you for helping us make the Elson Wealth Trading Platform secure for everyone!