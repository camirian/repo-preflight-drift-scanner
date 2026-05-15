# Sample Report Walkthrough

The included `examples/sample-repo` is intentionally messy. It exists so buyers can see what a blocked report looks like without scanning private work.

## Run the demo

```bash
make demo
```

or run directly:

```bash
python3 repo_preflight.py \
  --repo examples/sample-repo \
  --include-fixtures \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html \
  --out-sarif REPO_PREFLIGHT_REPORT.sarif
```

## Expected result

The sample should produce a `BLOCKED` decision.

That is correct. The point of the sample is to demonstrate findings and report structure.

## What to inspect

Open `REPO_PREFLIGHT_REPORT.md` first. Look for:

- the final decision
- blocker count
- warning count
- finding codes
- affected paths
- evidence, unless privacy mode is enabled

Then open `REPO_PREFLIGHT_REPORT.html` for a more readable browser view.

## What the sample teaches

The sample demonstrates that the scanner is conservative. It is designed to stop obvious release drift before it becomes public cleanup work.

## Buyer takeaway

A blocked report is not a failure of the tool. It is the tool doing its job. The correct loop is:

```text
scan -> inspect -> fix or accept -> rescan
```
