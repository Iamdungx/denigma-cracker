# Changelog

All notable changes to DEnigmaCracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-beta] - 2026-01-24

### Added

- **Complete architectural rewrite** with modern async/await pattern using `asyncio`
- **Concurrent processing** with multi-worker support for improved performance
- **Rich CLI interface** with beautiful terminal UI, colors, and live status updates
- **Enhanced security** with automatic seed phrase masking in logs
- **Multi-chain support** for Bitcoin, Ethereum, and BNB Smart Chain
- **YAML configuration** support alongside environment variables
- **Real-time statistics dashboard** showing scan progress and metrics
- **Token bucket rate limiting** algorithm for API rate limit compliance
- **Robust error handling** with retry mechanisms and graceful error recovery
- **Structured logging** with file and console output options
- **Modular package structure** with proper separation of concerns
- **Type hints** throughout the codebase for better type safety
- **Comprehensive documentation** including professional README and SECURITY.md
- **Test suite** with pytest for wallet generation and data models

### Changed

- Migrated from synchronous to asynchronous I/O architecture
- Refactored wallet generation to use proper BIP-39/BIP-44 implementations
- Improved API integration with Etherscan V2 API support
- Enhanced configuration management with Pydantic Settings
- Updated project structure to follow Python package best practices
- Improved error messages and user feedback

### Security

- Implemented automatic seed phrase masking in all log outputs
- Added explicit security disclaimers and usage restrictions
- Enhanced API key handling with secure environment variable management
- Added comprehensive security policy documentation

### Technical

- **Dependencies**: Upgraded to modern Python packages (aiohttp, pydantic, typer, rich)
- **Python version**: Requires Python 3.9 or higher
- **Package structure**: Proper `src/` layout with `__init__.py` files
- **Build system**: Added `pyproject.toml` for modern Python packaging

### Documentation

- Complete README.md rewrite with professional, academic tone
- Added SECURITY.md with responsible disclosure policy
- Enhanced inline code documentation
- Added usage examples and configuration guides

### Fixed

- Fixed potential race conditions in concurrent operations
- Improved rate limiting to prevent API throttling
- Enhanced error handling for network failures
- Fixed seed phrase masking edge cases

---

## [1.1] - Previous Version

### Note
Version 1.1 and earlier are no longer supported. Please upgrade to version 2.0-beta.

---

## [1.0] - Initial Release

Initial release of DEnigmaCracker.

---

[2.0.0-beta]: https://github.com/Iamdungx/DEnigma-Cracker/releases/tag/v2.0.0-beta
