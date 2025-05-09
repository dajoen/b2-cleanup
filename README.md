# B2 Cleanup

A CLI tool and Python library to clean up unfinished Backblaze B2 large file uploads.

[![PyPI version](https://badge.fury.io/py/b2-cleanup.svg)](https://badge.fury.io/py/b2-cleanup)
[![Python Versions](https://img.shields.io/pypi/pyversions/b2-cleanup.svg)](https://pypi.org/project/b2-cleanup/)

## 📋 Overview

When uploading large files to Backblaze B2, interrupted uploads can leave behind unfinished file parts that consume storage and incur costs. This tool helps you identify and clean up these unfinished uploads.

---

## 🔧 Features

- Lists all unfinished large file uploads in a given B2 bucket
- Optionally cancels them (dry-run support included)
- Uses the official `b2sdk` for native Backblaze API access
- Supports authentication via env vars, CLI override, or the `b2` CLI
- Smart bucket name suggestions with interactive correction
- Clean CLI with logging support
- Class-based and easily extensible

---

## 🚀 Installation

```bash
pip install b2-cleanup
```

---

## 🧪 Usage

```bash
# Basic usage (requires B2 CLI to be installed and authorized)
b2-cleanup your-bucket-name

# Use with explicit credentials
b2-cleanup your-bucket-name --key-id YOUR_KEY_ID --key YOUR_APPLICATION_KEY

# Dry run to preview what would be deleted
b2-cleanup your-bucket-name --dry-run

# Disable interactive prompts (for scripts/automation)
b2-cleanup your-bucket-name --non-interactive
```

### Example (dry run):

```bash
b2-cleanup my-bucket --dry-run
```

### Example (delete for real, with logging):

```bash
b2-cleanup my-bucket --log-file cleanup_$(date +%F).log
```

### Example (override credentials):

```bash
b2-cleanup my-bucket --key-id my-key-id --key my-app-key
```

### Example (interactive bucket correction):

If you mistype a bucket name, the tool wil suggest similar bucket names:

```bash
$ b2-cleanup misspelled-bucket-name
✅ Authorized with B2 CLI credentials.
⚠️ Bucket 'misspelled-bucket-name' not found. Did you mean 'correct-bucket-name'?
Use 'dajoen-backup-bucket' instead? [y/N]: y
✅ Using bucket 'misspelled-bucket-name' instead
🗃️ Found 2 unfinished uploads
🗑️ Cancelling file_id_123 (my-large-file.zip)
🗑️ Cancelling file_id_456 (another-large-file.iso)
```

### Example (Python usage):

```python
from b2_cleanup import B2CleanupTool

# Using environment variables or B2 CLI for auth
tool = B2CleanupTool(dry_run=True)

# Using explicit credentials
tool = B2CleanupTool(
    dry_run=False,
    override_key_id="your-key-id",
    override_key="your-application-key"
)

# Clean up unfinished uploads (with interactive mode)
tool.cleanup_unfinished_uploads("your-bucket-name", interactive=True)

# For scripts/automation (disable interactive prompts)
tool.cleanup_unfinished_uploads("your-bucket-name", interactive=False)
```

---

## 🔐 Authentication

This tool supports three ways to authenticate with B2, in priority order:

1. **Explicit CLI arguments**:
   ```bash
   b2-cleanup bucket-name --key-id YOUR_KEY_ID --key YOUR_APPLICATION_KEY
   ```

2. **Environment variables**:
   ```bash
   export B2_APPLICATION_KEY_ID=abc123
   export B2_APPLICATION_KEY=supersecretkey
   b2-cleanup bucket-name
   ```

3. **The `b2` CLI** (must be previously authorized):
   ```bash
   b2 account authorize
   # Then the tool will read credentials via:
   b2 account get
   ```

---

## 📁 Project Structure

```
b2-cleanup/
├── b2_cleanup/
│   ├── __init__.py     # Package exports
│   ├── core.py         # Core functionality 
│   └── cli.py          # CLI implementation
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── test_cli.py
├── pyproject.toml      # Project metadata + dependencies
├── CHANGELOG.md        # Version history
├── .gitignore
└── README.md
```

---

## 📦 Packaging Notes

- The CLI entry point is `b2-cleanup` via `pyproject.toml`
- Install in editable mode (`uv pip install -e .`) for fast development
- Dependencies are managed via [`uv`](https://github.com/astral-sh/uv)
- Testing dependencies: `uv pip install -e ".[dev]"`

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install b2-cleanup[dev]

# Run tests
pytest

# With coverage
pytest --cov=b2_cleanup
```

## 🛠️ Roadmap

- [ ] Filter uploads by file age
- [ ] Support multiple buckets
- [ ] Output metrics (count, size, cost saved)
- [ ] Optional integration with S3-compatible B2 APIs

---

## 📝 License

MIT License © 2025 Jeroen Verhoeven

