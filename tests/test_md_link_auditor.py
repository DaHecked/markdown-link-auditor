from pathlib import Path
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from md_link_auditor.core import audit_paths, extract_links, slugify_heading


def test_extract_links_ignores_code_and_images():
    text = '''
[good](docs/intro.md)
![image](logo.png)
`[not-a-link](missing.md)`
```md
[also-not](missing.md)
```
<https://example.com>
'''

    links = extract_links(text)

    assert [(link.label, link.target) for link in links] == [("good", "docs/intro.md")]


def test_slugify_heading_matches_common_github_style():
    assert slugify_heading("What's New in v2.0?") == "whats-new-in-v20"


def test_audit_paths_reports_broken_files_and_missing_anchors(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "README.md").write_text(
        "[intro](docs/intro.md)\n[missing](docs/missing.md)\n[bad anchor](docs/intro.md#nope)\n",
        encoding="utf-8",
    )
    (docs / "intro.md").write_text("# Getting Started\n", encoding="utf-8")

    report = audit_paths([tmp_path / "README.md"])

    assert report.ok is False
    assert [(item.target, item.status) for item in report.items] == [
        ("docs/intro.md", "ok"),
        ("docs/missing.md", "missing_file"),
        ("docs/intro.md#nope", "missing_anchor"),
    ]


def test_cli_json_returns_nonzero_for_broken_links(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("[missing](missing.md)\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "md_link_auditor", str(readme), "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["items"][0]["status"] == "missing_file"
