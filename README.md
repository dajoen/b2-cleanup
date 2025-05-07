# b2-cleanup

🧹 A Python CLI tool to clean up **unfinished large file uploads** in a [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html) bucket.

Built using [`b2sdk`](https://github.com/Backblaze/b2-sdk-python), [`click`](https://click.palletsprojects.com/), and [`uv`](https://github.com/astral-sh/uv) for performance and reproducibility.

---

## 🔧 Features

- Lists all unfinished large file uploads in a given B2 bucket
- Optionally cancels them (dry-run support included)
- Uses the official `b2sdk` for native Backblaze API access
- Supports authentication via env vars, CLI override, or the `b2` CLI
- Clean CLI with logging support
- Class-based and easily extensible

---

## 🚀 Installation

### 1. Clone and create an isolated environment

```bash
git clone https://github.com/<your-username>/b2-cleanup.git
cd b2-cleanup

uv venv
source .venv/bin/activate
uv pip install -e .
```

> Requires [uv](https://github.com/astral-sh/uv) and Python 3.8+

---

## 🧪 Usage

```bash
b2-cleanup BUCKET_NAME [OPTIONS]
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

---

## 🔐 Authentication

This tool supports three ways to authenticate with B2, in priority order:

1. **Explicit CLI arguments**:
   ```bash
   b2-cleanup my-bucket --key-id abc123 --key supersecretkey
   ```

2. **Environment variables**:
   ```bash
   export B2_APPLICATION_KEY_ID=abc123
   export B2_APPLICATION_KEY=supersecretkey
   ```

3. **The `b2` CLI** (must be previously authorized):
   ```bash
   b2 account authorize
   # Then the tool will read credentials via:
   b2 account info
   ```

---

## 📁 Project Structure

```
b2-cleanup/
├── cleanup_unfinished_b2_uploads.py   # Core CLI logic (class-based)
├── pyproject.toml                     # Project metadata + dependencies
├── .gitignore
└── README.md
```

---

## 📦 Packaging Notes

- The CLI entry point is `b2-cleanup` via `pyproject.toml`
- Install in editable mode (`uv pip install -e .`) for fast development
- Dependencies are managed via [`uv`](https://github.com/astral-sh/uv)

---

## 🛠️ Roadmap

- [ ] Filter uploads by file age
- [ ] Support multiple buckets
- [ ] Output metrics (count, size, cost saved)
- [ ] Optional integration with S3-compatible B2 APIs

---

## 📝 License

MIT License © 2025 Jeroen Verhoeven

