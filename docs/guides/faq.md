# Frequently Asked Questions

## General Questions

### What is Mrki?

Mrki is a powerful workflow automation platform that allows you to create, schedule, and monitor automated tasks and workflows. It provides a flexible plugin system, REST API, CLI tools, and a web interface.

### Is Mrki free to use?

Yes, Mrki is free for personal and non-commercial use under the Personal Use License. See the [LICENSE](../../LICENSE) file for details.

### What platforms does Mrki support?

Mrki supports:
- Linux (Ubuntu, Debian, CentOS, etc.)
- macOS (10.14+)
- Windows (10/11)
- Docker containers

### What are the system requirements?

**Minimum:**
- Python 3.9+
- 512 MB RAM
- 100 MB disk space

**Recommended:**
- Python 3.11+
- 2 GB RAM
- 1 GB disk space

## Installation

### How do I install Mrki?

```bash
pip install mrki
```

For detailed instructions, see the [Installation Guide](installation.md).

### Can I install Mrki without root access?

Yes, use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install mrki
```

Or install with `--user` flag:

```bash
pip install --user mrki
```

### How do I upgrade Mrki?

```bash
pip install --upgrade mrki
```

### How do I uninstall Mrki?

```bash
pip uninstall mrki
```

## Usage

### How do I start the Mrki server?

```bash
mrki server start
```

For background mode:

```bash
mrki server start --daemon
```

### How do I access the web interface?

Open your browser and navigate to `http://localhost:8080` (or your configured port).

### How do I create my first workflow?

Using CLI:

```bash
mrki workflow create --name my-workflow --file workflow.yaml
```

Using Python:

```python
import mrki
client = mrki.Client()
client.workflows.create(name="my-workflow", steps=[...])
```

### How do I schedule a workflow?

```bash
mrki schedule create \
  --name daily-task \
  --workflow my-workflow \
  --cron "0 9 * * *"
```

## Configuration

### Where is the configuration file located?

- **Linux/macOS**: `~/.config/mrki/config.yaml`
- **Windows**: `%APPDATA%\mrki\config.yaml`

### How do I change the default port?

Set via environment variable:

```bash
export MRKI_SERVER_PORT=9000
```

Or in config file:

```yaml
server:
  port: 9000
```

### How do I configure a database?

```yaml
database:
  url: postgresql://user:password@localhost/mrki
```

### How do I enable debug mode?

```bash
export MRKI_SERVER_DEBUG=true
```

Or:

```bash
mrki server start --debug
```

## Troubleshooting

### The server won't start

1. Check if the port is already in use:
   ```bash
   lsof -i :8080
   ```

2. Check the logs:
   ```bash
   mrki logs
   ```

3. Verify configuration:
   ```bash
   mrki config validate
   ```

### Database connection errors

1. Verify database URL format
2. Check network connectivity
3. Ensure database user has proper permissions
4. Check database logs

### Workflow execution fails

1. Check workflow definition syntax
2. Verify action parameters
3. Review execution logs
4. Test actions individually

### How do I reset Mrki to defaults?

```bash
# Stop the server
mrki server stop

# Remove configuration
rm -rf ~/.config/mrki

# Reinitialize
mrki init
```

## API

### How do I get an API key?

```bash
mrki api-key create --name my-key
```

### How do I authenticate API requests?

Include the API key in the header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8080/api/v1/workflows
```

### Is there a Python SDK?

Yes:

```bash
pip install mrki
```

```python
import mrki
client = mrki.Client(api_key="your-key")
```

### Is there a JavaScript SDK?

Yes:

```bash
npm install @mrki/sdk
```

```javascript
import { MrkiClient } from '@mrki/sdk';
const client = new MrkiClient({ apiKey: 'your-key' });
```

## Plugins

### How do I install plugins?

```bash
pip install mrki-plugin-name
```

### How do I create a custom plugin?

See the [Plugin Development Guide](plugins.md).

### Where are plugins stored?

Default location: `~/.config/mrki/plugins/`

### How do I enable/disable plugins?

In config file:

```yaml
plugins:
  enabled:
    - http
    - database
    # - disabled-plugin
```

## Security

### How do I enable authentication?

```yaml
security:
  enabled: true
  secret_key: "your-secret-key"
```

### How do I configure HTTPS?

```yaml
server:
  ssl:
    enabled: true
    cert_file: /path/to/cert.pem
    key_file: /path/to/key.pem
```

### How do I report a security vulnerability?

Please report security issues privately via [GitHub Security Advisories](https://github.com/mrki/mrki/security/advisories/new).

## Contributing

### How can I contribute?

See the [Contributing Guide](../../CONTRIBUTING.md).

### How do I report a bug?

Create an issue using the [bug report template](https://github.com/mrki/mrki/issues/new?template=bug_report.yml).

### How do I request a feature?

Create an issue using the [feature request template](https://github.com/mrki/mrki/issues/new?template=feature_request.yml).

## Support

### Where can I get help?

- 📖 [Documentation](https://mrki.readthedocs.io)
- 💬 [Discussions](https://github.com/mrki/mrki/discussions)
- 🐛 [Issue Tracker](https://github.com/mrki/mrki/issues)

### Is there commercial support available?

Yes, enterprise support is available. Contact us at enterprise@mrki.dev.

## Licensing

### Can I use Mrki for commercial projects?

The Personal Use License restricts commercial use. Contact us for commercial licensing options.

### Can I modify Mrki?

Yes, you can modify Mrki for personal use. See the LICENSE file for details.

### Can I distribute Mrki?

Distribution is restricted under the Personal Use License. Contact us for redistribution rights.
