# ASReview 5-Star

Enhanced systematic review tools with stopping rules, IRR, meta-analysis, and PRISMA support.

## Features

- **Stopping Rules**: Bayesian, SPRT, SAFE, and consecutive irrelevant methods
- **Inter-Rater Reliability**: Cohen's Kappa, Fleiss' Kappa, Krippendorff's Alpha
- **Meta-Analysis**: Effect pooling, heterogeneity statistics, publication bias tests
- **PRISMA**: Flow diagram statistics and SVG generation
- **REST API**: FastAPI-based HTTP endpoints for integration
- **CLI**: Command-line interface for common operations

## Installation

```bash
pip install asreview-5star

# With API support
pip install asreview-5star[api]

# With all extras
pip install asreview-5star[all]
```

## Quick Start

### Stopping Rules

```python
import asreview_5star as a5s

# Bayesian stopping rule
result = a5s.bayesian_stopping(
    n_screened=500,
    n_relevant=25,
    n_total=5000,
    target_recall=0.95
)

print(f"Should stop: {result.should_stop}")
print(f"Confidence: {result.confidence:.2%}")
```

### Inter-Rater Reliability

```python
# Cohen's Kappa for two raters
rater1 = [1, 1, 0, 0, 1, 0, 1, 0]
rater2 = [1, 0, 0, 0, 1, 0, 1, 0]

result = a5s.cohens_kappa(rater1, rater2)
print(f"Kappa: {result.coefficient:.3f}")
print(f"Interpretation: {result.interpretation}")
```

### Meta-Analysis

```python
import math

# Pool effect sizes (log hazard ratios)
effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
ses = [0.1, 0.12, 0.11]

result = a5s.pool_effects(effects, ses, model="random")
print(f"Pooled HR: {math.exp(result.pooled_effect):.3f}")
print(f"I-squared: {result.heterogeneity['I_squared']:.1f}%")
```

### PRISMA Statistics

```python
stats = a5s.prisma_stats(
    records_total=1000,
    records_duplicates=100,
    records_screened=900,
    records_excluded_screening=800,
    records_retrieved=100,
    records_not_retrieved=5,
    records_excluded_fulltext=70
)

print(f"Studies included: {stats.studies_included}")
```

## REST API

Start the API server:

```bash
asreview-5star serve --port 8000
```

Then make requests:

```bash
curl -X POST http://localhost:8000/api/v1/stopping/bayesian \
  -H "Content-Type: application/json" \
  -d '{"n_screened": 500, "n_relevant": 25, "n_total": 5000}'
```

API documentation available at `http://localhost:8000/docs`

## CLI

```bash
# Calculate stopping probability
asreview-5star stopping --method bayesian --screened 500 --relevant 25 --total 5000

# Calculate IRR from CSV
asreview-5star irr --method kappa --file ratings.csv

# Generate PRISMA statistics
asreview-5star prisma --total 1000 --duplicates 100 --screened 900 \
  --excluded-screening 800 --retrieved 100 --excluded-fulltext 70
```

## Documentation

- [Getting Started Notebook](notebooks/01_getting_started.ipynb)
- [Stopping Rules Comparison](notebooks/02_stopping_rules_comparison.ipynb)
- [Meta-Analysis Workflow](notebooks/03_meta_analysis_workflow.ipynb)
- [Audit & Certification](notebooks/04_audit_certification.ipynb)
- [FAQ](docs/FAQ.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## API Reference

### Stopping Rules

| Function | Description |
|----------|-------------|
| `bayesian_stopping()` | Posterior probability of target recall |
| `sprt_stopping()` | Sequential Probability Ratio Test |
| `safe_stopping()` | Stop After First Estimate procedure |
| `consecutive_irrelevant_stopping()` | Threshold-based stopping |

### IRR

| Function | Description |
|----------|-------------|
| `cohens_kappa()` | Agreement between two raters |
| `fleiss_kappa()` | Agreement among multiple raters |
| `krippendorff_alpha()` | Reliability with missing data |
| `percent_agreement()` | Simple agreement percentage |

### Meta-Analysis

| Function | Description |
|----------|-------------|
| `pool_effects()` | Fixed/random effects pooling |
| `eggers_test()` | Publication bias (regression) |
| `beggs_test()` | Publication bias (rank correlation) |
| `heterogeneity_stats()` | I², tau², Q statistics |
| `forest_plot_data()` | Data for forest plot visualization |

### PRISMA

| Function | Description |
|----------|-------------|
| `prisma_stats()` | Calculate flow diagram statistics |
| `prisma_flow_data()` | Structured data for visualization |
| `generate_prisma_svg()` | Generate SVG flow diagram |

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{asreview_5star,
  title = {ASReview 5-Star: Enhanced Systematic Review Tools},
  author = {ASReview Team},
  year = {2024},
  url = {https://github.com/asreview/asreview-5star}
}
```
