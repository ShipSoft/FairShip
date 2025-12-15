#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""
Generate a PR comment summarizing physics metrics comparison results.

This script processes comparison artifacts from all matrix configurations and
generates a concise summary for posting as a PR comment.
"""

import argparse
import sys
from pathlib import Path


def parse_comparison_file(comparison_file):
    """
    Parse a comparison result file and extract summary.

    Returns a dict with:
    - status: 'no_reference', 'no_diff', or 'has_diff'
    - total_differences: int
    - summary: dict with comparison stats
    - differences: list of difference descriptions
    """
    content = comparison_file.read_text()

    if "No reference metrics found" in content:
        return {
            "status": "no_reference",
            "message": "No reference metrics available (first run)",
        }

    if "No significant differences found" in content:
        # Parse summary from the output
        summary = {}
        for line in content.split("\n"):
            if "Files compared:" in line:
                summary["files"] = int(line.split(":")[1].strip())
            elif "Histograms compared:" in line:
                summary["histograms"] = int(line.split(":")[1].strip())
            elif "Fits compared:" in line:
                summary["fits"] = int(line.split(":")[1].strip())

        return {"status": "no_diff", "summary": summary}

    # Parse differences
    differences = []
    total_diff = 0
    summary = {}

    in_diff_section = False
    current_file = None

    for line in content.split("\n"):
        if "Files compared:" in line:
            summary["files"] = int(line.split(":")[1].strip())
        elif "Histograms compared:" in line:
            summary["histograms"] = int(line.split(":")[1].strip())
        elif "Fits compared:" in line:
            summary["fits"] = int(line.split(":")[1].strip())
        elif "Total differences:" in line:
            total_diff = int(line.split(":")[1].strip())

        if "Differences found:" in line:
            in_diff_section = True
            continue

        if in_diff_section:
            if line.strip().endswith(":") and not line.startswith("  "):
                current_file = line.strip().rstrip(":")
            elif line.strip() and current_file and line.startswith("  "):
                differences.append({"file": current_file, "description": line.strip()})

    return {
        "status": "has_diff",
        "total_differences": total_diff,
        "summary": summary,
        "differences": differences,
    }


def generate_comment(comparison_dir):
    """Generate markdown PR comment from comparison results."""
    comparison_files = list(Path(comparison_dir).glob("comparison_*.txt"))

    if not comparison_files:
        return "No comparison results found"

    results = {}
    for comp_file in comparison_files:
        parts = comp_file.stem.replace("comparison_", "").split("_")
        if len(parts) >= 4:
            vessel = parts[0]
            snd = parts[1]
            shield = "_".join(parts[2:-1])
            target = parts[-1]
            config = f"{vessel}-{snd}-{shield}-{target}"
        else:
            config = comp_file.stem

        results[config] = parse_comparison_file(comp_file)

    lines = ["## Physics Metrics Comparison", ""]

    no_ref = sum(1 for r in results.values() if r["status"] == "no_reference")
    no_diff = sum(1 for r in results.values() if r["status"] == "no_diff")
    has_diff = sum(1 for r in results.values() if r["status"] == "has_diff")

    if no_ref == len(results):
        lines.append("**First run**: No reference metrics available yet")
    elif has_diff == 0:
        lines.append(
            "**All configurations match reference** (no significant differences)"
        )
    else:
        lines.append(f"**{has_diff} configuration(s) have differences**")

    lines.append("")
    lines.append(f"- Configurations compared: {len(results)}")
    if no_ref > 0:
        lines.append(f"- No reference available: {no_ref}")
    if no_diff > 0:
        lines.append(f"- Matching reference: {no_diff}")
    if has_diff > 0:
        lines.append(f"- With differences: {has_diff}")

    # Detailed results for configurations with differences
    if has_diff > 0:
        lines.append("")
        lines.append("### Configurations with Differences")
        lines.append("")

        for config, result in sorted(results.items()):
            if result["status"] != "has_diff":
                continue

            lines.append(f"#### `{config}`")
            lines.append("")

            summary = result.get("summary", {})
            total_diff = result.get("total_differences", 0)

            lines.append(f"- Files compared: {summary.get('files', 0)}")
            lines.append(f"- Histograms compared: {summary.get('histograms', 0)}")
            lines.append(f"- Fits compared: {summary.get('fits', 0)}")
            lines.append(f"- **Total differences: {total_diff}**")
            lines.append("")

            differences = result.get("differences", [])
            if differences:
                lines.append("<details>")
                lines.append("<summary>Show differences</summary>")
                lines.append("")
                lines.append("```")

                by_file = {}
                for diff in differences:
                    file = diff["file"]
                    if file not in by_file:
                        by_file[file] = []
                    by_file[file].append(diff["description"])

                for file, file_diffs in sorted(by_file.items()):
                    lines.append(f"{file}:")
                    for desc in file_diffs[:5]:
                        lines.append(f"  {desc}")
                    if len(file_diffs) > 5:
                        lines.append(f"  ... and {len(file_diffs) - 5} more")
                    lines.append("")

                lines.append("```")
                lines.append("</details>")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>About this comparison</summary>")
    lines.append("")
    lines.append("Physics metrics are extracted from ROOT files and compared.")
    lines.append("Default comparison uses 5% tolerance for histogram statistics")
    lines.append("and 3σ for fit parameters.")
    lines.append("")
    lines.append(
        "Metrics stored in git notes: `refs/notes/ci/physics-metrics/<config>`"
    )
    lines.append("</details>")

    return "\n".join(lines)


def main():
    """Generate PR comment from comparison results."""
    parser = argparse.ArgumentParser(
        description="Generate PR comment from comparison results"
    )
    parser.add_argument(
        "comparison_dir",
        help="Directory containing comparison_*.txt files",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file for comment markdown (default: stdout)",
    )

    args = parser.parse_args()

    comment = generate_comment(args.comparison_dir)

    if args.output:
        Path(args.output).write_text(comment)
        print(f"Comment written to {args.output}")
    else:
        print(comment)

    return 0


if __name__ == "__main__":
    sys.exit(main())
