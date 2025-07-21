# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

1. **DO NOT** open a public issue
2. Email security concerns to: [maintainer-email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Best Practices

When using Telegram MCP Server:

1. **Environment Variables**
   - Never commit `.env` files
   - Use secure methods to manage secrets
   - Rotate tokens regularly

2. **Authentication**
   - Always configure `TELEGRAM_CHAT_ID`
   - Use strong, unique bot tokens
   - Monitor for unauthorized access attempts

3. **Deployment**
   - Run in isolated environments
   - Use HTTPS for all communications
   - Keep dependencies updated
   - Enable logging for audit trails

4. **Rate Limiting**
   - Implement rate limiting in production
   - Monitor for abuse patterns
   - Set appropriate timeouts

## Response Timeline

- Initial response: Within 48 hours
- Status update: Within 1 week
- Fix deployment: Based on severity

Thank you for helping keep Telegram MCP Server secure!