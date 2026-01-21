# Physics Metrics Tracking with Git Notes

This directory contains scripts for tracking physics metrics across CI runs using Git notes.

## Overview

The metrics tracking system provides lightweight monitoring of simulation and reconstruction outputs:

- **Metrics extraction** (~8KB JSON per configuration vs 10MB+ ROOT files)
- **Git notes storage** (metrics attached to commits, don't clutter history)
- **Self-documenting comparison** (each metric specifies its comparison mode)
- **Automated CI integration** (runs on every PR and master commit)

## JSON Format

Each metric in the JSON specifies its comparison mode:

```json
{
  "entries": {
    "value": 100,
    "compare": "exact"
  },
  "mean": {
    "value": 22.87,
    "uncertainty": 2.49,
    "compare": "statistical"
  },
  "integral": {
    "value": 39.0,
    "compare": "float"
  }
}
```

**Comparison modes:**
- `exact`: Values must match exactly (integers, strings)
- `float`: Floating-point comparison with relative tolerance
- `statistical`: Compare within combined statistical uncertainties

## Configuration

### `metrics_config.yaml`

The configuration file controls what metrics are extracted and comparison tolerances.

```yaml
files:
  # ROOT files to process
  process:
    - sim_ci-test.root
    - sim_ci-test_rec.root
    - sim_ci-test_ana.root
    - recohists.root

extraction:
  max_histogram_depth: 2              # Directory recursion depth
  fit_functions:                      # Fit functions to search for
    - gaus
    - pol1
    - expo

comparison:
  float_tolerance: 1.0e-9  # Relative tolerance for float comparisons
  n_sigma: 3.0             # Sigma threshold for statistical comparisons
```

**Customization:**
- Add/remove files in `files.process` to change which ROOT files are processed
- Modify `fit_functions` to search for different fit function names
- Adjust `max_histogram_depth` to control how deep into directory structures to search
- Change default comparison tolerances in `comparison` section

## Scripts

### `extract_physics_metrics.py`

Extracts lightweight physics metrics from ROOT files with comparison modes and uncertainties.

**Usage:**
```bash
python extract_physics_metrics.py <config_dir> [-o OUTPUT] [--pretty]
```

**Extracts:**
- Tree information: entries (exact), branches (exact)
- Histogram statistics: entries, mean, RMS (statistical with uncertainties), integral (float)
- Fit parameters: values with uncertainties (statistical)
- File sizes for reference

**Example:**
```bash
# Extract metrics from current directory using default config
python extract_physics_metrics.py . -o metrics.json --pretty

# Extract from specific configuration
python extract_physics_metrics.py test_output/ -o test_metrics.json

# Use custom config file
python extract_physics_metrics.py . -o metrics.json --config custom_config.yaml
```

### `compare_metrics.py`

Compares two metrics JSON files respecting the comparison mode specified for each metric.

**Usage:**
```bash
python compare_metrics.py <reference.json> <new.json> [options]
```

**Options:**
- `--float-tolerance FLOAT`: Relative tolerance for float comparisons (default: 1e-9)
- `--n-sigma FLOAT`: Number of sigma for statistical comparisons (default: 3.0)
- `--fail-on-diff`: Exit with code 1 if differences found

**Comparison logic:**
- **exact mode**: Values must match exactly
- **float mode**: Relative difference $|\frac{v_{\text{new}} - v_{\text{ref}}}{v_{\text{ref}}}| <$ `--float-tolerance`
- **statistical mode**: Deviation $\frac{|v_{\text{new}} - v_{\text{ref}}|}{\sqrt{\sigma_{\text{ref}}^2 + \sigma_{\text{new}}^2}} <$ `--n-sigma`

**Example:**
```bash
# Default comparison (uses tolerances from metrics_config.yaml)
python compare_metrics.py reference.json new.json

# Override float tolerance
python compare_metrics.py reference.json new.json --float-tolerance 1e-6

# Override statistical threshold
python compare_metrics.py reference.json new.json --n-sigma 2.0

# Use custom config file
python compare_metrics.py reference.json new.json --config custom_config.yaml

# Fail CI if differences found
python compare_metrics.py reference.json new.json --fail-on-diff
```

## CI Integration

### Workflow Overview

The CI workflow has three jobs for metrics tracking:

1. **`run-sim-chain`**: Extracts metrics after simulation/reconstruction
   - Runs for all matrix configurations
   - Uploads metrics as artifacts

2. **`store-metrics`**: Stores metrics in git notes (master branch only)
   - Downloads metrics artifacts
   - Stores in `refs/notes/ci/physics-metrics/<config>`
   - Pushes to remote

3. **`compare-metrics`**: Compares PR metrics with base branch (PRs only)
   - Fetches git notes from base commit
   - Compares with PR metrics
   - Uploads comparison results

### Git Notes Structure

Metrics are stored in separate note refs for each configuration:

```
refs/notes/ci/physics-metrics/vacuums-all-New_HA_Design-old
refs/notes/ci/physics-metrics/vacuums-all-New_HA_Design-Jun25
refs/notes/ci/physics-metrics/helium-all-warm_opt-old
...
```

### Viewing Stored Metrics

```bash
# Fetch all metrics notes
git fetch origin 'refs/notes/ci/physics-metrics/*:refs/notes/ci/physics-metrics/*'

# View metrics for a specific commit and configuration
git notes --ref=ci/physics-metrics/vacuums-all-New_HA_Design-old show <commit-sha>

# List all commits with metrics
git log --show-notes=ci/physics-metrics/vacuums-all-New_HA_Design-old
```

### Manual Comparison

```bash
# Compare current working directory with reference commit
COMMIT=abc123def
CONFIG=vacuums-all-New_HA_Design-old

# Extract current metrics
python .github/scripts/extract_physics_metrics.py . -o current.json

# Get reference metrics
git notes --ref=ci/physics-metrics/$CONFIG show $COMMIT > reference.json

# Compare
python .github/scripts/compare_metrics.py reference.json current.json
```

## Customising Metrics

### Configuration Changes (No Code Required)

Most customizations can be made by editing `metrics_config.yaml`:

1. **Change which files are processed**: Modify `files.process` list
2. **Add/remove fit functions**: Modify `extraction.fit_functions` list
3. **Adjust histogram search depth**: Change `extraction.max_histogram_depth`
4. **Change default tolerances**: Modify `comparison` values

These changes take effect immediately without modifying Python code.

### Adding New Metric Types (Code Changes)

To extract entirely new types of metrics, edit `extract_physics_metrics.py`:

1. Modify `extract_histogram_stats()` to add new histogram-based metrics
2. Modify `extract_tree_info()` to add new tree-based metrics
3. Add new extraction functions for other ROOT objects

Each metric should specify:
```python
{
    "value": <number>,
    "compare": "exact" | "float" | "statistical",
    "uncertainty": <number>  # only for "statistical" mode
}
```

### Comparison Modes

When adding new metrics, choose the comparison mode:
- `"exact"`: Integers that must match exactly (event counts, detector IDs)
- `"float"`: Floating-point values without physics uncertainties
- `"statistical"`: Values with physics uncertainties

### Overriding Tolerances

Use command-line flags to override config defaults:
- `--float-tolerance`: For numerical precision (config default: $10^{-9}$)
- `--n-sigma`: For statistical significance (config default: $3.0\sigma$)

## Benefits Over Full ROOT Comparison

1. **Storage**: ~8KB vs 10MB+ per configuration
2. **Speed**: Instant JSON parsing vs ROOT file I/O
3. **History**: Git notes provide complete timeline
4. **Scalability**: Works with 16 matrix configurations (8 × 2 × 2 × 2)
5. **Accessibility**: JSON readable without ROOT

## Complementary Approach

This metrics tracking complements the full ROOT file comparison:

- **Git notes metrics**: Quick check on every commit (~130KB total for all configs)
- **Full ROOT comparison**: Detailed validation with reference files stored in git-lfs

Use metrics for continuous monitoring and full comparison for detailed debugging.
