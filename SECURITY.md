# Security Policy

## Supported Versions

The following versions of Mrki are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:

1. **GitHub Security Advisories**: [Create a security advisory](https://github.com/mrki/mrki/security/advisories/new)
2. **Email**: security@mrki.dev

### What to Include

When reporting a vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: Assessment of the potential impact
- **Affected Versions**: Which versions are affected
- **Mitigation**: Any known workarounds or mitigations
- **Contact Information**: How we can reach you for clarifications

### Response Timeline

We aim to respond to security reports within:

- **24 hours**: Acknowledgment of receipt
- **72 hours**: Initial assessment and response
- **7 days**: Fix or mitigation plan
- **30 days**: Public disclosure (if applicable)

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version of Mrki
2. **Secure Configuration**:
   - Change default passwords
   - Use strong API keys
   - Enable authentication
   - Configure HTTPS in production
3. **Network Security**:
   - Use firewalls to restrict access
   - Don't expose Mrki directly to the internet without proper security
4. **Secrets Management**:
   - Don't commit secrets to version control
   - Use environment variables for sensitive data
   - Rotate API keys regularly

### For Developers

1. **Input Validation**: Always validate and sanitize user input
2. **Authentication**: Ensure all endpoints are properly protected
3. **Authorization**: Implement proper access controls
4. **Logging**: Log security-relevant events
5. **Dependencies**: Keep dependencies updated
6. **Testing**: Include security tests in your test suite

## Security Features

Mrki includes several security features:

- **Authentication**: API key and JWT-based authentication
- **Authorization**: Role-based access control
- **Rate Limiting**: Configurable rate limits
- **Input Validation**: Pydantic-based request validation
- **HTTPS Support**: TLS/SSL configuration
- **Audit Logging**: Security event logging
- **CORS**: Configurable Cross-Origin Resource Sharing

## Known Security Considerations

### Default Configuration

The default configuration is designed for development. For production:

- Change the default secret key
- Enable authentication
- Configure HTTPS
- Set up proper firewall rules

### Plugin Security

Plugins execute with the same privileges as Mrki:

- Only install plugins from trusted sources
- Review plugin code before installation
- Use sandboxing where possible

### Database Security

- Use strong database passwords
- Limit database user privileges
- Enable SSL for database connections
- Regular database backups

## Security Updates

Security updates will be:

1. Released as soon as possible
2. Documented in the changelog
3. Announced via GitHub releases
4. Posted on our security mailing list

## Acknowledgments

We thank the following security researchers for their responsible disclosures:

- [Your name could be here!]

## Contact

For security-related questions:

- Email: security@mrki.dev
- GPG Key: [Download](https://mrki.dev/security.gpg)

---

Last updated: January 2024
