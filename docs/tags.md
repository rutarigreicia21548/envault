# Project Tags

envault lets you attach **tags** to projects so you can organise, filter, and
search across many `.env` sets.

## Concepts

- A tag is a non-empty string (whitespace is stripped automatically).
- Each project stores its tags in `<storage_dir>/<project>/tags.json`.
- Tags are deduplicated and sorted alphabetically on save.

## Python API

```python
from envault.tags import add_tag, remove_tag, get_tags, find_projects_by_tag

storage = ".envault"

# Add tags
add_tag(storage, "my-api", "production")
add_tag(storage, "my-api", "backend")

# List tags
print(get_tags(storage, "my-api"))  # ['backend', 'production']

# Remove a tag
remove_tag(storage, "my-api", "backend")

# Find all projects carrying a tag
projects = find_projects_by_tag(storage, "production")
print(projects)  # ['my-api', 'payments-service', ...]
```

## Overwriting the full tag list

```python
from envault.tags import set_tags

set_tags(storage, "my-api", ["staging", "frontend"])
```

## Errors

| Situation | Exception |
|---|---|
| Adding an empty/whitespace-only tag | `TagError` |
| Removing a tag that does not exist | `TagError` |
| Writing tags to a project directory that does not exist | `TagError` |
| Corrupt `tags.json` | `TagError` |

All exceptions are instances of `envault.tags.TagError`.

## Storage layout

```
.envault/
  my-api/
    data.enc
    tags.json       ← ["production", "backend"]
  payments-service/
    data.enc
    tags.json       ← ["production", "frontend"]
```
