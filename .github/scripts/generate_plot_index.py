#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Generate an HTML index page and PR comment from rendered plot manifests."""

import argparse
import json
import sys
from pathlib import Path


def collect_manifests(base_dir: Path) -> list[dict]:
    """Find and load all manifest.json files under base_dir.

    Each file entry gets its path prefixed with the manifest's
    subdirectory relative to base_dir, so paths work from the
    top-level index.html.
    """
    manifests = []
    for manifest_path in sorted(base_dir.rglob("manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        rel_dir = manifest_path.parent.relative_to(base_dir)
        for entry in manifest.get("files", []):
            entry["file"] = str(rel_dir / entry["file"])
        manifests.append(manifest)
    return manifests


def generate_html(manifests: list[dict], title: str) -> str:
    """Generate a self-contained HTML page from manifests."""
    sections = []
    for manifest in manifests:
        job = manifest["job"]
        config = manifest["config"]
        plots = manifest.get("files", [])
        if not plots:
            continue

        heading = f"{job} ({config})"
        images = []
        for plot in plots:
            images.append(
                f'<figure><img src="{plot["file"]}" alt="{plot["name"]}"'
                f' loading="lazy"><figcaption>{plot["name"]}'
                f' <span class="type">({plot["type"]})</span>'
                f"</figcaption></figure>"
            )
        sections.append(f"<h2>{heading}</h2>\n<div class='grid'>{''.join(images)}</div>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #fafafa; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: 0.5rem; }}
  h2 {{ color: #555; margin-top: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1rem; }}
  figure {{ margin: 0; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 0.5rem; }}
  img {{ width: 100%; height: auto; }}
  figcaption {{ text-align: center; padding: 0.25rem; font-size: 0.9rem; }}
  .type {{ color: #888; }}
</style>
</head>
<body>
<h1>{title}</h1>
{"".join(sections)}
</body>
</html>"""


def generate_comment(manifests: list[dict], base_url: str) -> str:
    """Generate a markdown PR comment body."""
    lines = ["<!-- ci-plots-comment -->", "## CI Plots", ""]
    lines.append(f"**[View all plots]({base_url}/index.html)**")
    lines.append("")

    for manifest in manifests:
        job = manifest["job"]
        config = manifest["config"]
        plots = manifest.get("files", [])
        if not plots:
            continue

        lines.append(f"### {job} ({config})")
        lines.append("")
        # Show first 3 plots inline, rest in details
        inline = plots[:3]
        rest = plots[3:]
        for plot in inline:
            lines.append(f"![{plot['name']}]({base_url}/{plot['file']})")
            lines.append("")
        if rest:
            lines.append("<details><summary>More plots</summary>")
            lines.append("")
            for plot in rest:
                lines.append(f"![{plot['name']}]({base_url}/{plot['file']})")
                lines.append("")
            lines.append("</details>")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    """Generate HTML index and PR comment from plot manifests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plot_dir", help="Directory containing plot images and manifests")
    parser.add_argument("--title", default="CI Plots", help="Page title")
    parser.add_argument("--base-url", default=".", help="Base URL for image links in comment")
    parser.add_argument("--output-html", default=None, help="Output HTML path (default: plot_dir/index.html)")
    parser.add_argument("--output-comment", default=None, help="Output comment path (default: plot_dir/comment.md)")
    args = parser.parse_args()

    plot_dir = Path(args.plot_dir)
    manifests = collect_manifests(plot_dir)

    if not manifests:
        print("No manifests found, nothing to generate.", file=sys.stderr)
        return 0

    html_path = Path(args.output_html) if args.output_html else plot_dir / "index.html"
    html_path.write_text(generate_html(manifests, args.title))
    print(f"Index page written to {html_path}")

    comment_path = Path(args.output_comment) if args.output_comment else plot_dir / "comment.md"
    comment_path.write_text(generate_comment(manifests, args.base_url))
    print(f"Comment written to {comment_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
