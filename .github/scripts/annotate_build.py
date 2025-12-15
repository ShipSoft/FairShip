#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

"""Parse compiler output and create GitHub annotations."""

import re
import sys
from pathlib import Path


def parse_compiler_output(line):
    """
    Parse GCC/Clang compiler output line.

    Expected format:
    /path/to/file.cpp:line:col: severity: message [flag]

    Returns dict with file, line, col, severity, message, flag or None if no match.
    """
    # Pattern for GCC/Clang warnings and errors
    pattern = r"^(.+?):(\d+):(\d+):\s+(warning|error|note):\s+(.+?)(?:\s+\[(.+?)\])?$"
    match = re.match(pattern, line.strip())

    if not match:
        return None

    file_path, line_num, col_num, severity, message, flag = match.groups()

    return {
        "file": file_path,
        "line": int(line_num),
        "col": int(col_num),
        "severity": severity,
        "message": message,
        "flag": flag,
    }


def make_relative_path(file_path, repo_name="FairShip"):
    """
    Convert absolute path to relative path from repo root.

    aliBuild creates paths like:
    /__w/FairShip/FairShip/sw/SOURCES/FairShip/master/0/shipdata/ShipHit.cxx

    We need to extract the part after 'SOURCES/FairShip/master/0/'
    """
    # Strip any aliBuild debug prefix
    # (format: "YYYY-MM-DD@HH:MM:SS:DEBUG:package:package:N: ")
    # This prefix appears before the actual file path
    if ":" in file_path and not file_path.startswith("/"):
        # Find the last occurrence of ": /" which separates the prefix from the path
        path_start = file_path.rfind(": /")
        if path_start != -1:
            file_path = file_path[path_start + 2 :]  # Skip ": " to get the path

    path = Path(file_path)
    parts = path.parts

    # Look for the pattern: SOURCES/FairShip/master/0/...
    try:
        sources_idx = parts.index("SOURCES")
        # Verify this is followed by FairShip/master/0
        if (
            sources_idx + 3 < len(parts)
            and parts[sources_idx + 1] == repo_name
            and parts[sources_idx + 2] == "master"
            and parts[sources_idx + 3] == "0"
        ):
            # Extract everything after SOURCES/FairShip/master/0/
            relative_parts = parts[sources_idx + 4 :]
            if relative_parts:
                return str(Path(*relative_parts))
    except (ValueError, IndexError):
        pass

    # Fallback: try to find FairShip in checkout directory (FairShip/)
    try:
        # Find last occurrence of FairShip (to skip workspace path)
        for i in range(len(parts) - 1, -1, -1):
            if parts[i] == repo_name:
                # Skip this FairShip and everything after it is the relative path
                relative_parts = parts[i + 1 :]
                if relative_parts:
                    return str(Path(*relative_parts))
                break
    except (ValueError, IndexError):
        pass

    # If we can't parse it, return the filename
    return path.name


def create_annotation(parsed, repo_dir="FairShip"):
    """
    Create GitHub annotation command from parsed compiler output.

    Format: ::severity file={file},line={line},col={col},title={title}::{message}
    """
    # Convert to relative path
    rel_path = make_relative_path(parsed["file"], repo_dir)

    # Map 'note' to 'notice' for GitHub
    severity = parsed["severity"]
    if severity == "note":
        severity = "notice"

    # Build title from flag if available
    title = parsed["flag"] if parsed["flag"] else parsed["severity"]

    # Escape special characters in message
    message = (
        parsed["message"].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    )

    # Create annotation command
    annotation = (
        f"::{severity} "
        f"file={rel_path},"
        f"line={parsed['line']},"
        f"col={parsed['col']},"
        f"title={title}"
        f"::{message}"
    )

    return annotation


def main():
    """Parse stdin and output annotations."""
    annotation_count = {"error": 0, "warning": 0, "notice": 0}

    for line in sys.stdin:
        # Print original line for logging
        print(line, end="", file=sys.stderr)

        # Try to parse as compiler output
        parsed = parse_compiler_output(line)

        if parsed:
            # Create and output annotation
            annotation = create_annotation(parsed)
            print(annotation)

            # Track counts
            severity = parsed["severity"]
            if severity == "note":
                severity = "notice"
            annotation_count[severity] = annotation_count.get(severity, 0) + 1

    # Print summary
    print("\n--- Annotation Summary ---", file=sys.stderr)
    print(f"Errors: {annotation_count['error']}", file=sys.stderr)
    print(f"Warnings: {annotation_count['warning']}", file=sys.stderr)
    print(f"Notices: {annotation_count['notice']}", file=sys.stderr)


if __name__ == "__main__":
    main()
