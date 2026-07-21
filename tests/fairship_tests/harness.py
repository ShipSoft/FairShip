# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Run shell-configured tests and compare their terminal output."""

from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parent.parent
TEST_CASES = HERE / "test_cases.yaml"
SKIP_PATTERNS = HERE / "skip_patterns.conf"
VALID_TEST_NAME = re.compile(r"[A-Za-z0-9_.-]+")
TEST_TIMEOUT_SECONDS = 30 * 60


@dataclass(frozen=True)
class TestCase:
    name: str
    script: Path
    reference: Path
    dependencies: tuple[str, ...]


def test_cases() -> list[TestCase]:
    """Return and validate the tests declared by the configuration file."""
    try:
        configuration = yaml.safe_load(TEST_CASES.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise RuntimeError(f"Invalid YAML in {TEST_CASES}: {error}") from error

    if not isinstance(configuration, dict) or set(configuration) != {"tests"}:
        raise RuntimeError(f"{TEST_CASES} must contain exactly one top-level 'tests' key")
    configured_tests = configuration["tests"]
    if not isinstance(configured_tests, list) or not configured_tests:
        raise RuntimeError(f"'tests' in {TEST_CASES} must be a non-empty list")

    cases: list[TestCase] = []
    for index, configured_test in enumerate(configured_tests, start=1):
        location = f"{TEST_CASES} test #{index}"
        if isinstance(configured_test, dict) and set(configured_test) == {"name"}:
            name = configured_test["name"]
            dependencies = []
        elif isinstance(configured_test, dict) and set(configured_test) == {"name", "depends_on"}:
            name = configured_test["name"]
            dependencies = configured_test["depends_on"]
        else:
            raise RuntimeError(
                f"{location} must be a test name or a mapping containing 'name' and optional 'depends_on'"
            )
        if not isinstance(name, str) or not name:
            raise RuntimeError(f"{location} must be a non-empty test name")
        if VALID_TEST_NAME.fullmatch(name) is None:
            raise RuntimeError(f"Invalid test name {name!r} in {location}")
        if not isinstance(dependencies, list) or not all(
            isinstance(dependency, str) and dependency for dependency in dependencies
        ):
            raise RuntimeError(f"'depends_on' in {location} must be a list of non-empty test names")
        if len(dependencies) != len(set(dependencies)):
            raise RuntimeError(f"Duplicate dependencies for {name!r} in {location}")

        script = (HERE / "scripts" / f"{name}.sh").resolve()
        reference = (HERE / "references" / f"{name}.txt").resolve()
        if not script.is_file():
            raise RuntimeError(f"Test script does not exist for {name!r}: {script}")
        if not script.stat().st_mode & 0o111:
            raise RuntimeError(f"Test script is not executable for {name!r}: {script}")

        cases.append(TestCase(name=name, script=script, reference=reference, dependencies=tuple(dependencies)))

    names = [case.name for case in cases]
    if len(names) != len(set(names)):
        raise RuntimeError(f"Duplicate test names in {TEST_CASES}")

    known_names = set(names)
    seen_names: set[str] = set()
    for case in cases:
        unknown = set(case.dependencies) - known_names
        if unknown:
            raise RuntimeError(f"Unknown dependencies for {case.name!r} in {TEST_CASES}: {', '.join(sorted(unknown))}")
        if case.name in case.dependencies:
            raise RuntimeError(f"Test {case.name!r} cannot depend on itself in {TEST_CASES}")
        later = set(case.dependencies) - seen_names
        if later:
            raise RuntimeError(
                f"Dependencies for {case.name!r} must appear earlier in {TEST_CASES}: {', '.join(sorted(later))}"
            )
        seen_names.add(case.name)

    cases_by_name = {case.name: case for case in cases}
    visited: set[str] = set()
    visiting: list[str] = []

    def validate_acyclic(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            cycle = visiting[visiting.index(name) :] + [name]
            raise RuntimeError(f"Dependency cycle in {TEST_CASES}: {' -> '.join(cycle)}")
        visiting.append(name)
        for dependency in cases_by_name[name].dependencies:
            validate_acyclic(dependency)
        visiting.pop()
        visited.add(name)

    for name in names:
        validate_acyclic(name)

    return cases


def test_names() -> list[str]:
    """Return the configured test names."""
    return [case.name for case in test_cases()]


def dependency_groups() -> dict[str, str]:
    """Map every test to its dependency-connected CTest working-directory group."""
    cases = test_cases()
    neighbours = {case.name: set(case.dependencies) for case in cases}
    for case in cases:
        for dependency in case.dependencies:
            neighbours[dependency].add(case.name)

    groups: dict[str, str] = {}
    for case in cases:
        if case.name in groups:
            continue
        group_name = case.name
        pending = [case.name]
        while pending:
            name = pending.pop()
            if name in groups:
                continue
            groups[name] = group_name
            pending.extend(neighbours[name])
    return groups


def _test_case(test_name: str) -> TestCase:
    try:
        return next(case for case in test_cases() if case.name == test_name)
    except StopIteration:
        raise RuntimeError(f"Unknown FairShip test: {test_name}") from None


def _compile_wildcard(pattern: str) -> re.Pattern[str]:
    """Compile a full-line pattern in which only ``*`` is special."""
    expression = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.compile(expression)


def _patterns_for(test_name: str) -> list[re.Pattern[str]]:
    known_tests = set(test_names())
    patterns: list[str] = []
    current_selector: str | None = None
    for line_number, raw_line in enumerate(SKIP_PATTERNS.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if raw_line.startswith("test "):
            current_selector = line.removeprefix("test ").strip()
            if not current_selector:
                raise RuntimeError(f"Missing test name in {SKIP_PATTERNS}:{line_number}")
            if current_selector != "*" and current_selector not in known_tests:
                raise RuntimeError(f"Unknown test name {current_selector!r} in {SKIP_PATTERNS}:{line_number}")
        elif not raw_line[:1].isspace():
            raise RuntimeError(f"Expected 'test NAME' or an indented pattern in {SKIP_PATTERNS}:{line_number}")
        elif current_selector is None:
            raise RuntimeError(f"Pattern outside a test block in {SKIP_PATTERNS}:{line_number}")
        elif current_selector in {"*", test_name}:
            patterns.append(line)

    return [_compile_wildcard(pattern) for pattern in patterns]


def run(test_name: str, workdir: Path) -> tuple[int, str]:
    """Run one configured test, returning its status and normalized output."""
    case = _test_case(test_name)
    environment = os.environ.copy()
    environment["FAIRSHIP_ROOT"] = str(REPOSITORY_ROOT)
    try:
        result = subprocess.run(
            [str(case.script)],
            cwd=workdir,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TEST_TIMEOUT_SECONDS,
        )
        returncode = result.returncode
        stdout = result.stdout
    except subprocess.TimeoutExpired as error:
        returncode = 124
        stdout = error.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        stdout += f"\nTest timed out after {TEST_TIMEOUT_SECONDS} seconds\n"
    patterns = _patterns_for(test_name)
    lines = stdout.splitlines(keepends=True)
    output = "".join(line for line in lines if not any(pattern.fullmatch(line.rstrip("\r\n")) for pattern in patterns))
    return returncode, output


def assert_matches_reference(test_name: str, workdir: Path, prepare: bool) -> None:
    """Run one test and compare its output with its reference."""
    if prepare:
        shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True, exist_ok=True)
    returncode, output = run(test_name, workdir)
    if returncode != 0:
        raise RuntimeError(f"{test_name} exited with status {returncode}\n\n{output}")

    path = _test_case(test_name).reference
    if not path.exists():
        raise RuntimeError(f"Missing reference file {path}. Run {HERE / 'regenerate_references.sh'}.")
    expected = path.read_text(encoding="utf-8")
    diff = "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            output.splitlines(keepends=True),
            fromfile=str(path),
            tofile=f"{test_name} (current output)",
        )
    )
    if diff:
        raise RuntimeError(f"Terminal output changed for {test_name}:\n\n{diff}")


def regenerate() -> None:
    """Replace all reference files with current successful output."""
    completed: set[str] = set()
    temporary_root = Path(tempfile.mkdtemp(prefix="fairship-tests-"))

    def regenerate_test(name: str) -> None:
        if name in completed:
            return
        case = _test_case(name)
        for dependency in case.dependencies:
            regenerate_test(dependency)

        workdir = temporary_root / dependency_groups()[name]
        workdir.mkdir(parents=True, exist_ok=True)
        returncode, output = run(name, workdir)
        if returncode != 0:
            raise RuntimeError(
                f"{case.name} exited with status {returncode}; references were not fully regenerated\n\n{output}"
            )
        case.reference.parent.mkdir(parents=True, exist_ok=True)
        case.reference.write_text(output, encoding="utf-8")
        print(f"wrote {case.reference}")
        completed.add(name)

    try:
        for case in test_cases():
            regenerate_test(case.name)
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)


def emit_cmake() -> None:
    """Emit validated test declarations consumed by tests/CMakeLists.txt."""
    cases = test_cases()
    groups = dependency_groups()
    group_members: dict[str, list[str]] = {}
    for case in cases:
        group_members.setdefault(groups[case.name], []).append(case.name)
    for case in cases:
        members = group_members[groups[case.name]]
        dependencies = list(case.dependencies)
        if case.name != members[0] and members[0] not in dependencies:
            dependencies.append(members[0])
        if case.name == members[-1]:
            dependencies.extend(name for name in members[:-1] if name not in dependencies)
        dependency_arguments = " ".join(f'"{dependency}"' for dependency in dependencies)
        lifecycle = " PREPARE" if case.name == members[0] else ""
        lifecycle += " CLEANUP" if case.name == members[-1] else ""
        print(
            f'fairship_add_regression_test(NAME "{case.name}" '
            f'GROUP "{groups[case.name]}"{lifecycle} DEPENDS {dependency_arguments})'
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--regenerate", action="store_true", help="replace reference files with current output")
    actions.add_argument("--emit-cmake", action="store_true", help="write CTest declarations to standard output")
    actions.add_argument("--run", metavar="NAME", help="run and validate one configured test")
    parser.add_argument("--workdir", type=Path, help="working directory used with --run")
    parser.add_argument("--prepare", action="store_true", help="clean the work directory before running")
    parser.add_argument("--cleanup", action="store_true", help="remove the work directory after running")
    args = parser.parse_args()
    if args.regenerate:
        regenerate()
    elif args.emit_cmake:
        emit_cmake()
    elif args.run:
        if args.workdir is None:
            parser.error("--run requires --workdir")
        workdir = args.workdir.resolve()
        try:
            assert_matches_reference(args.run, workdir, args.prepare)
        finally:
            if args.cleanup:
                shutil.rmtree(workdir, ignore_errors=True)
    else:
        parser.error("no action requested")


if __name__ == "__main__":
    main()
