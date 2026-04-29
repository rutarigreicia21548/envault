# envault

> Lightweight secrets manager that syncs `.env` files with encrypted remote storage.

---

## Installation

```bash
pip install envault
```

---

## Usage

**Push your local `.env` to remote storage:**

```bash
envault push --env .env --vault my-project
```

**Pull and decrypt secrets to a local `.env`:**

```bash
envault pull --vault my-project --out .env
```

**Use directly in Python:**

```python
from envault import load_vault

load_vault("my-project")  # Loads secrets into os.environ
```

**Initialize a new vault with an encryption key:**

```bash
envault init --vault my-project --key-file ~/.envault/key
```

Secrets are encrypted with AES-256 before being sent to remote storage. Supported backends include S3, GCS, and Azure Blob Storage.

---

## Configuration

Set your backend in `~/.envault/config.toml`:

```toml
[storage]
backend = "s3"
bucket  = "my-secrets-bucket"
region  = "us-east-1"
```

---

## License

[MIT](LICENSE) © 2024 envault contributors