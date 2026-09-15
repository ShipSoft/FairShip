# FairShip regression tests

These CTest tests run shell scripts declared in `test_cases.yaml` and compare
their combined standard output and standard error with configured reference
files.

To add a test:

1. Add a `name` mapping to the `tests` list in `test_cases.yaml`.
2. Create an executable `scripts/TEST_NAME.sh` file containing the test
   command.
3. Reconfigure CMake and run `tests/fairship_tests/regenerate_references.sh`.
4. Review and commit the generated `references/TEST_NAME.txt` file.

Each YAML entry is a mapping containing a test name:

```yaml
tests:
  - name: example
```

To order a test after other tests, use a mapping with `name` and `depends_on`:

```yaml
tests:
  - name: simulation
  - name: reconstruction
    depends_on:
      - simulation
```

Dependencies may themselves have dependencies. The harness validates that
every dependency exists and rejects dependency cycles. CTest's `DEPENDS`
property orders selected prerequisites before their dependents; it does not
prevent a dependent from running after a prerequisite fails. It also does not
select prerequisites excluded by a CTest name or label filter. Run the complete
regression suite when testing dependency-connected cases.

Prerequisites must be listed before their dependents in `test_cases.yaml`.
Dependency-connected tests share a working directory and a resource lock, so
they run sequentially without file races. Independent groups can run
concurrently.

For a test named `example`, the harness automatically uses:

- `scripts/example.sh` as the executable test script.
- `references/example.txt` as the expected terminal output.

Test names may contain letters, numbers, dots, underscores, and hyphens. The
script filename and reference filename must use exactly the same test name.

Test scripts run in build-tree working directories organized by dependency
group. Tests in the same dependency-connected graph share a directory, while
unrelated groups are isolated. During a complete suite run, the harness creates
a clean directory before each group and removes it afterward. Filtered or
interrupted runs can leave a directory behind.

The harness sets `FAIRSHIP_ROOT` to the repository root. Scripts should use it
when referring to repository files:

```sh
python "$FAIRSHIP_ROOT/macro/example.py"
```

Relative input and output paths inside a test script refer to the temporary
working directory.

To preserve working directories for inspection, configure with:

```sh
cmake -S . -B build -DFAIRSHIP_KEEP_TEST_OUTPUT=ON
```

Without this option, directories are deleted after their complete groups run.

Run the tests with:

```sh
ctest --test-dir build --output-on-failure --parallel 4 -L regression
# or
pixi run test-fairship
```

Regenerate every reference after an intentional output change with:

```sh
tests/fairship_tests/regenerate_references.sh
# or
pixi run regenerate-fairship-references
```

Several configured scripts download remote input files, so the complete suite
and reference regeneration require network access.

`skip_patterns.conf` contains full-line wildcard patterns for output that is
expected to vary. An asterisk (`*`) matches any text; all other characters are
matched literally. Start a block with `test NAME` and list its patterns on the
following lines. Use `test *` for patterns that apply to every test. Use this
sparingly, because skipped lines are excluded from validation.
