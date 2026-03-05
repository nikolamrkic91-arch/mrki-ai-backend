# Installation Guide

This guide covers various methods to install and set up Mrki on your system.

## Prerequisites

- Python 3.9 or higher
- pip or conda package manager
- (Optional) Docker and Docker Compose

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install Mrki is using pip:

```bash
pip install mrki
```

Install with optional dependencies:

```bash
# With web interface support
pip install mrki[web]

# With database support
pip install mrki[database]

# With all features
pip install mrki[all]
```

### Method 2: Install from Source

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/mrki/mrki.git
cd mrki

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Method 3: Using Docker

Run Mrki using Docker:

```bash
# Pull the image
docker pull mrki/mrki:latest

# Run the container
docker run -p 8080:8080 mrki/mrki:latest
```

### Method 4: Using Docker Compose

For a complete development environment:

```bash
# Clone the repository
git clone https://github.com/mrki/mrki.git
cd mrki

# Start all services
docker-compose up -d
```

## Platform-Specific Instructions

### Linux

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip build-essential

# Install Mrki
pip3 install mrki
```

### macOS

```bash
# Using Homebrew
brew install python@3.11

# Install Mrki
pip3 install mrki
```

### Windows

```powershell
# Using PowerShell
python -m pip install --upgrade pip
pip install mrki
```

## Verification

Verify the installation:

```bash
# Check version
mrki --version

# Run health check
mrki health

# Start the server
mrki server start
```

## Configuration

### Initial Setup

1. Create a configuration directory:

```bash
mkdir -p ~/.config/mrki
```

2. Create a basic configuration file:

```bash
cat > ~/.config/mrki/config.yaml << EOF
server:
  host: 0.0.0.0
  port: 8080
  debug: false

database:
  url: sqlite:///~/.config/mrki/mrki.db

logging:
  level: INFO
  format: json
EOF
```

### Environment Variables

You can also configure Mrki using environment variables:

```bash
export MRKI_SERVER_HOST=0.0.0.0
export MRKI_SERVER_PORT=8080
export MRKI_DATABASE_URL=postgresql://user:pass@localhost/mrki
export MRKI_LOG_LEVEL=DEBUG
```

## Development Installation

For contributing to Mrki:

```bash
# Clone the repository
git clone https://github.com/mrki/mrki.git
cd mrki

# Install development dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
make lint
```

## Troubleshooting

### Common Issues

#### Permission Denied

```bash
# Use --user flag
pip install --user mrki

# Or use a virtual environment
python -m venv venv
source venv/bin/activate
pip install mrki
```

#### Import Errors

```bash
# Reinstall with dependencies
pip install --force-reinstall mrki[all]
```

#### Database Connection Issues

```bash
# Check database URL format
export MRKI_DATABASE_URL=postgresql://user:password@host:port/database

# Test connection
mrki db check
```

### Getting Help

If you encounter issues:

1. Check the [FAQ](faq.md)
2. Search [existing issues](https://github.com/mrki/mrki/issues)
3. Join our [Discussions](https://github.com/mrki/mrki/discussions)
4. Create a new issue with the bug report template

## Next Steps

- Read the [User Guide](usage.md) to learn how to use Mrki
- Explore the [Configuration Guide](configuration.md)
- Check out the [API Reference](../api/index.md)
