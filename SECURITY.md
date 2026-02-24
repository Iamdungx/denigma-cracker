# Security Policy

## Supported Versions

The following versions of DEnigmaCracker are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0-beta | :white_check_mark: |
| 1.1   | :x:                |
| 1.0  | :x:                |

**Note**: Only the latest version receives active security updates. Users are strongly encouraged to upgrade to the latest version.

---

## Scope of Security Concerns

We take security seriously and welcome responsible disclosure of security vulnerabilities. The following areas are within scope for security reporting:

### In-Scope Security Issues

- **Authentication and Authorization**: Vulnerabilities related to API key handling, authentication mechanisms, or unauthorized access to user data
- **Data Protection**: Issues related to seed phrase or sensitive data exposure in logs, memory, or files
- **Input Validation**: Vulnerabilities that could lead to code injection, path traversal, or other injection attacks
- **Cryptographic Implementation**: Flaws in the implementation of BIP-39/BIP-44 key derivation that could compromise security
- **API Security**: Vulnerabilities in how the tool interacts with blockchain APIs (e.g., credential leakage, request manipulation)
- **Dependency Vulnerabilities**: Known security vulnerabilities in project dependencies that could affect users
- **Configuration Security**: Issues that could lead to unintended exposure of sensitive configuration data

### Out-of-Scope Issues

The following are **NOT** considered security vulnerabilities:

- **Mathematical Infeasibility**: Reports about the mathematical impossibility of finding funded wallets through random generation are expected behavior, not vulnerabilities
- **Rate Limiting**: API rate limits imposed by blockchain service providers are intentional and not security issues
- **Educational Purpose Limitations**: The tool's inability to realistically find funded wallets is by design and not a security concern
- **Feature Requests**: Requests for new features or functionality improvements
- **Performance Issues**: Performance problems that do not have security implications
- **Documentation Issues**: Typos, unclear documentation, or missing documentation (unless it leads to security risks)

---

## Critical Usage Restrictions

**IMPORTANT**: This tool must **NEVER** be used to attempt access to cryptocurrency wallets that you do not own or do not have explicit written permission to access.

### Prohibited Activities

- Attempting to access wallets belonging to others
- Using the tool to attempt unauthorized access to any cryptocurrency wallet
- Any use that violates applicable laws or regulations
- Any use that violates the terms of service of blockchain API providers

### Legal and Ethical Responsibility

Users are solely responsible for ensuring their use of this tool complies with:
- All applicable local, state, and federal laws
- Terms of service of blockchain API providers (Etherscan, BscScan, Blockchain.info)
- Ethical guidelines for security research

**The authors and maintainers of this project assume no liability for misuse of this software.**

---

## Risks and Limitations

### Known Risks

1. **API Key Exposure**: API keys stored in environment variables or configuration files could be exposed if not properly secured
   - **Mitigation**: Use secure environment variable management and never commit API keys to version control

2. **Seed Phrase Logging**: While the tool implements seed phrase masking, improper configuration could lead to exposure
   - **Mitigation**: Always use the default seed masking settings and review log files before sharing

3. **Network Security**: API requests are made over HTTPS, but network-level attacks could potentially intercept traffic
   - **Mitigation**: Use secure networks and consider VPN usage for sensitive research environments

4. **Dependency Vulnerabilities**: Third-party dependencies may contain security vulnerabilities
   - **Mitigation**: Keep dependencies updated and monitor security advisories

### Limitations

- This tool does not implement any security bypass mechanisms
- The tool operates entirely within standard BIP-39/BIP-44 protocols
- No cryptographic weaknesses are exploited
- The tool cannot realistically find funded wallets due to mathematical constraints

---

## Reporting a Vulnerability

We appreciate responsible disclosure of security vulnerabilities. If you discover a security issue, please follow these steps:

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. **Email** security concerns to: `buidxng299@gmail.com`
3. **Include** the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact and severity assessment
   - Suggested fix (if available)
   - Your contact information for follow-up

### What to Expect

- **Initial Response**: We aim to acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability within 7 days
- **Updates**: We will provide regular updates on the status of the vulnerability
- **Resolution**: We will work to resolve critical vulnerabilities as quickly as possible
- **Disclosure**: We will coordinate disclosure timing with the reporter

### Responsible Disclosure Timeline

- **Critical vulnerabilities**: We aim to release a patch within 7-14 days
- **High severity**: We aim to release a patch within 30 days
- **Medium/Low severity**: We aim to address within 90 days

**Note**: Timeline may vary based on complexity and availability of maintainers.

### Recognition

With your permission, we will acknowledge your responsible disclosure in:
- Security advisories
- Release notes
- Project documentation

---

## Security Best Practices for Users

### API Key Management

- Store API keys in environment variables, not in code or configuration files
- Use separate API keys for different environments (development, testing, production)
- Rotate API keys regularly
- Never commit API keys to version control

### Logging and Data Protection

- Review log files before sharing or publishing
- Ensure seed phrase masking is enabled (default setting)
- Securely delete log files when no longer needed
- Be cautious when sharing screenshots or terminal output

### Network Security

- Use secure, trusted networks when running the tool
- Consider using VPN for additional security
- Monitor network traffic for unusual activity

### System Security

- Keep your operating system and Python environment updated
- Use virtual environments to isolate dependencies
- Regularly update project dependencies: `pip install -r requirements.txt --upgrade`
- Run the tool with minimal necessary privileges

### Configuration Security

- Review configuration files before use
- Use `.env` files (not committed to version control) for sensitive data
- Validate configuration settings before running the tool

---

## Security Updates

Security updates will be released as:
- **Patch versions** (e.g., 2.0.1) for security fixes
- **Security advisories** published on GitHub
- **Release notes** documenting security-related changes

Users are strongly encouraged to:
- Subscribe to repository notifications
- Monitor the GitHub Security tab
- Keep the tool and its dependencies updated

---

## Contact

For security-related inquiries:
- **Email**: `buidxng299@gmail.com`
- **Subject Line**: `[SECURITY] DEnigmaCracker - [Brief Description]`

For non-security issues, please use the [GitHub Issues](https://github.com/Iamdungx/DEnigma-Cracker/issues) page.

---

## Acknowledgments

We thank the security research community for their responsible disclosure practices and contributions to improving the security of this project.

---

**Last Updated**: 2026-01-24
