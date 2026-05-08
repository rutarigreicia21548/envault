# Access Policies

Envault supports per-project **access policies** that restrict which secret keys
may be read or written. Policies are stored as `policy.json` inside the
project's storage directory and are evaluated locally before any vault operation.

## Policy fields

| Field | Type | Description |
|---|---|---|
| `allowed_keys` | `list[str]` | If non-empty, only these keys are permitted. |
| `denied_keys` | `list[str]` | These keys are always blocked, even if in `allowed_keys`. |
| `read_only` | `bool` | When `true`, all write operations (`push`, `rotate`) are rejected. |
| `require_tags` | `dict[str, str]` | Reserved for future tag-based enforcement. |

## Example `policy.json`

```json
{
  "allowed_keys": ["DB_URL", "REDIS_URL", "SECRET_KEY"],
  "denied_keys": [],
  "read_only": false,
  "require_tags": {}
}
```

## Programmatic usage

```python
from pathlib import Path
from envault.policy import Policy, save_policy, load_policy, enforce, check_env

storage = Path(".envault")

# Create and persist a policy
policy = Policy(allowed_keys=["DB_URL", "API_KEY"], read_only=False)
save_policy("my-project", policy, storage)

# Load and enforce
policy = load_policy("my-project", storage)
if policy:
    enforce(policy, "DB_URL", write=True)   # raises PolicyError if denied

# Validate an entire env dict at once
violations = check_env(policy, env_dict, write=True)
if violations:
    for v in violations:
        print("Policy violation:", v)
```

## Behaviour notes

- If `allowed_keys` is **empty**, all keys are permitted (unless explicitly denied).
- `denied_keys` takes precedence over `allowed_keys`.
- A missing `policy.json` means **no restrictions** — `load_policy` returns `None`
  and callers should treat that as an open policy.
