# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2025-05-09

### Added
- Comprehensive test suite with pytest
- Code coverage reporting
- Project restructured as a proper installable module
- Added support for importing the tool as a library
- Better error handling for missing B2 CLI
- CLI entry point for easy command-line usage
- Testing dependencies in dev extras

### Fixed
- Fixed attribute error when accessing UnfinishedLargeFile properties
- Corrected TOML syntax in pyproject.toml (replaced // comments with #)
- Proper packaging configuration with Hatchling

### Changed
- Split code into core.py and cli.py modules
- Improved project structure for better maintainability
- Enhanced logging with more descriptive messages

## [0.1.3] - 2025-05-08

### Added
- Initial public release
- Basic functionality to clean up unfinished large file uploads in B2 buckets
- Support for authentication via CLI arguments, environment variables, or B2 CLI
- Dry run mode to preview what would be deleted