.PHONY: test demo package release-check clean

PYTHON ?= python3
VERSION ?= v0.4
PACKAGE_NAME ?= ai-agent-repo-preflight-kit-$(VERSION)
RELEASE_DIR ?= release

REPORTS = \
	REPO_PREFLIGHT_REPORT.md \
	REPO_PREFLIGHT_REPORT.json \
	REPO_PREFLIGHT_REPORT.html \
	REPO_PREFLIGHT_REPORT.sarif \
	REPORT.md \
	REPORT.json \
	REPORT.html \
	REPORT.sarif \
	VERIFY_ACTION_REPORT.md \
	VERIFY_ACTION_REPORT.json \
	VERIFY_ACTION_REPORT.html \
	VERIFY_ACTION_REPORT.sarif \
	VERIFY_BASELINE_REPORT.md \
	VERIFY_BASELINE_REPORT.json \
	VERIFY_DOCS_REPORT.md \
	VERIFY_DOCS_REPORT.json \
	VERIFY_ERROR_REPORT.md \
	VERIFY_ERROR_REPORT.json \
	VERIFY_LOCAL_ACTION_REPORT.md \
	VERIFY_LOCAL_ACTION_REPORT.json \
	VERIFY_LOCAL_ACTION_REPORT.html \
	VERIFY_LOCAL_ACTION_REPORT.sarif \
	VERIFY_OPPORTUNITY_BOARD_DOCS_REPORT.md \
	VERIFY_OPPORTUNITY_BOARD_DOCS_REPORT.json \
	VERIFY_PARANOID_REPORT.md \
	VERIFY_PARANOID_REPORT.json \
	VERIFY_PUBLIC_EXPORT_REPORT.md \
	VERIFY_PUBLIC_EXPORT_REPORT.json \
	VERIFY_RULE_PACK_REPORT.md \
	VERIFY_RULE_PACK_REPORT.json \
	VERIFY_SELF_REPORT.md \
	VERIFY_SELF_REPORT.json \
	VERIFY_SELF_REPORT.html

test:
	$(PYTHON) verify_scanner.py

demo:
	$(PYTHON) repo_preflight.py \
		--repo examples/sample-repo \
		--include-fixtures \
		--out-md REPO_PREFLIGHT_REPORT.md \
		--out-json REPO_PREFLIGHT_REPORT.json \
		--out-html REPO_PREFLIGHT_REPORT.html \
		--out-sarif REPO_PREFLIGHT_REPORT.sarif || true
	@echo "Demo reports written: REPO_PREFLIGHT_REPORT.md/.json/.html/.sarif"

package:
	bash scripts/package_release.sh $(VERSION)

release-check: test package
	@test -f $(RELEASE_DIR)/$(PACKAGE_NAME).zip
	@echo "Release package ready: $(RELEASE_DIR)/$(PACKAGE_NAME).zip"

clean:
	rm -f $(REPORTS)
	rm -rf $(RELEASE_DIR)/$(PACKAGE_NAME) $(RELEASE_DIR)/$(PACKAGE_NAME).zip
