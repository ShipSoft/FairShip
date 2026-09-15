# FairShip tests

The `tests` directory contains two complementary test suites:

- C++ unit and I/O tests registered with CTest.
- Shell-driven regression tests, implemented by a Python harness and registered
  with CTest, that compare terminal output with committed reference files.

## Default CTest suite

The following command builds FairShip and runs the original C++ tests used by
the default GitHub CI pipeline. Regression tests are opt-in:

Using Pixi:

```sh
pixi run test
```

With an existing configured build directory:

```sh
cmake --build build
ctest --test-dir build --output-on-failure -LE regression
```

## C++ tests

The C++ tests are declared in `tests/CMakeLists.txt`, built with FairShip, and
registered with CTest. To run one by name:

```sh
ctest --test-dir build --output-on-failure -R DataClassIO
```

New C++ tests should be added as executables in `tests/CMakeLists.txt` and
registered with `add_test()`.

## FairShip regression tests

The `fairship_tests` suite runs shell-configured commands, captures their
combined standard output and standard error, and compares the result with
reference text files committed under `fairship_tests/references`.

Run the suite with:

```sh
ctest --test-dir build --output-on-failure --parallel 4 -L regression
```

or:

```sh
pixi run test-fairship
```

### Adding a FairShip regression test

All FairShip regression tests are configured in
`fairship_tests/test_cases.yaml`. To add a test:

1. Add a `name` mapping to the `tests` list in `test_cases.yaml`.
2. Create an executable `fairship_tests/scripts/TEST_NAME.sh` file containing
   the command.
3. Regenerate the reference files.
4. Review and commit the generated
   `fairship_tests/references/TEST_NAME.txt` file.

Test names may contain letters, numbers, dots, underscores, and hyphens.
A nonzero exit status fails the test, even if its output matches the reference.

Each YAML entry is a mapping containing a test name:

```yaml
tests:
  - name: example
```

Tests that depend on other tests use `name` and `depends_on`:

```yaml
tests:
  - name: simulation
  - name: reconstruction
    depends_on:
      - simulation
```

Unknown dependencies, self-dependencies, duplicate dependencies, and dependency
cycles are rejected as configuration errors. When the complete suite is
selected, CTest runs each prerequisite once and orders the dependent test after
it.

CTest's `DEPENDS` property controls execution order only: a dependent test is
still attempted if a prerequisite fails. It also does not add a prerequisite
that was excluded by a test-name or label filter. Run the complete regression
suite when testing dependency-connected cases.

List every prerequisite before its dependents in `test_cases.yaml`. The first
test in each connected dependency group prepares its shared directory and the
last cleans it; listing a dependent first can produce conflicting CTest
ordering constraints.

CTest dependency properties and resource locks run dependency-connected
tests sequentially in one working directory. Independent groups use isolated
directories and can execute concurrently.

For each test name, the harness automatically locates:

- The executable script at `fairship_tests/scripts/TEST_NAME.sh`.
- The reference output at `fairship_tests/references/TEST_NAME.txt`.

The script and reference filenames must use exactly the configured test name.

FairShip regression scripts execute in temporary working directories organized
by dependency group under the build tree. Outputs from dependencies remain
available to dependent tests, unrelated groups are isolated, and the harness
removes generated files after the complete group runs. Filtered or interrupted
runs can leave a working directory behind.

The harness provides the repository root through the `FAIRSHIP_ROOT`
environment variable. Scripts should use it for repository-relative programs
and input files:

```sh
python "$FAIRSHIP_ROOT/macro/example.py"
```

Other relative paths resolve inside the temporary working directory.

Configure CMake to preserve those directories for inspection:

```sh
cmake -S . -B build -DFAIRSHIP_KEEP_TEST_OUTPUT=ON
```

Without the option, these directories are removed after a complete group run.

### Nondeterministic output

`fairship_tests/skip_patterns.conf` contains full-line wildcard patterns for
lines that should be excluded from comparison. An asterisk (`*`) matches any
text, while all other characters are matched literally. Start a block with
`test NAME` and list its patterns on the following lines. Use `test *` for
patterns that apply to every test:

```ini
test *
  Timestamp: *

test example-test
  Processing time: * s
```

Patterns must match the complete line. Keep them as narrow as possible because
matching lines are removed before validation.

### Regenerating references

After an intentional output change, regenerate all reference files with:

```sh
tests/fairship_tests/regenerate_references.sh
```

or:

```sh
pixi run regenerate-fairship-references
```

The regeneration command updates the configured reference file for every test.
Always review the resulting diff before committing it.

Several configured commands download remote input files, so running or
regenerating the complete regression suite requires network access.

More implementation details are available in
[`fairship_tests/README.md`](fairship_tests/README.md).
