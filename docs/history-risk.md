# History Risk

Status: release gate documentation

This repository is published as a clean single-commit export. It carries no prior Git history, so there is no historical-blob exposure to remediate in this repository.

## Fixture And Detection Note

- The scanner detects secret-bearing filenames (for example, a tracked `credentials.json`) by name only. It never reads or prints secret file contents.
- The `examples/sample-repo` fixture is intentionally messy so the scanner has something to flag during demos and tests. Any secret-looking names or terms in the scanner's rules and fixtures are detection vocabulary, not real secrets.

## If You Fork And Build History

If you continue development and accumulate history, keep secrets out of the tree from the first commit. Use the scanner's `public-export` profile before sharing:

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid
```

Filename-only history audit (lists paths and counts only, never prints blob contents):

```bash
git log --all --name-only --pretty=format: | sed '/^$/d' | sort -u
```

If a real secret ever lands in history, rotate or revoke the affected credential. Treat rotation as separate from any Git history cleanup.
