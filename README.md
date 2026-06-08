# markdown-link-auditor

Scan Markdown documentation for broken local links and missing heading anchors.

`markdown-link-auditor` is a small CLI for OSS maintainers who want confidence that README and docs links still work before cutting a release.

## Features

- Extract Markdown inline links while ignoring fenced code blocks and inline code
- Validate local file links and `#heading-anchor` fragments
- Skip `mailto:`, `tel:`, and other non-file schemes
- Optional JSON report for CI
- Dependency-free Python package with tests

## Quick start

```bash
pip install -e .
md-link-auditor README.md docs --json
```

## Exit codes

- `0`: no broken local links
- `1`: one or more broken local links or anchors

## License

MIT
