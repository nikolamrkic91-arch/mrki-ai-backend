# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements

## [1.0.0] - 2024-01-15

### Added
- Initial release of Mrki
- Core workflow engine with dependency management
- REST API with authentication (API key and JWT)
- CLI interface for workflow management
- Web dashboard for visual workflow management
- Plugin system for custom actions
- Task scheduler with cron expression support
- Database support (SQLite, PostgreSQL, MySQL)
- Built-in actions (HTTP, database, email, file operations)
- Workflow templates
- Execution monitoring and logging
- Configuration management
- Docker and Docker Compose support
- Comprehensive documentation
- GitHub Actions CI/CD pipelines

### Security
- API key authentication
- JWT token authentication
- Rate limiting
- CORS configuration
- Input validation

## [0.9.0] - 2024-01-01 (Beta)

### Added
- Beta release for testing
- Core workflow execution
- Basic REST API
- CLI tools
- SQLite support
- Plugin architecture

### Changed
- Refactored core engine for better performance

### Fixed
- Various bugs from alpha testing

## [0.8.0] - 2023-12-01 (Alpha)

### Added
- Alpha release for internal testing
- Proof of concept workflow engine
- Basic API endpoints
- Simple CLI

---

## Release Notes Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes
```

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2024-01-15 | Current |
| 0.9.0 | 2024-01-01 | Beta |
| 0.8.0 | 2023-12-01 | Alpha |

---

## Contributing to Changelog

When making changes, add an entry under the `[Unreleased]` section:

1. Choose the appropriate category (Added, Changed, Deprecated, Removed, Fixed, Security)
2. Write a clear, concise description
3. Reference issue/PR numbers when applicable

Example:
```markdown
### Added
- New webhook action for real-time notifications (#123)
```
