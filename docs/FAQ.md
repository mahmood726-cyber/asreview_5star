# ASReview 5-Star FAQ

Frequently asked questions about ASReview 5-Star.

## Table of Contents

- [General Questions](#general-questions)
- [Stopping Rules](#stopping-rules)
- [Inter-Rater Reliability](#inter-rater-reliability)
- [Meta-Analysis](#meta-analysis)
- [PRISMA](#prisma)
- [Integration](#integration)

---

## General Questions

### What is ASReview 5-Star?

ASReview 5-Star is a Python package that provides enhanced tools for systematic review workflows, including:

- **Stopping rules**: Bayesian, SPRT, SAFE, and consecutive irrelevant methods
- **IRR calculations**: Cohen's Kappa, Fleiss' Kappa, Krippendorff's Alpha
- **Meta-analysis**: Effect pooling, heterogeneity statistics, publication bias tests
- **PRISMA**: Flow diagram statistics and visualization

### How does ASReview 5-Star relate to ASReview LAB?

ASReview 5-Star is a complementary package that can be used alongside ASReview LAB. While ASReview LAB handles active learning for screening prioritization, ASReview 5-Star provides:

- Stopping rule calculations to determine when screening can end
- IRR metrics for dual screening validation
- Meta-analysis tools for quantitative synthesis
- PRISMA statistics for reporting

### What Python versions are supported?

ASReview 5-Star requires Python 3.8 or higher.

### How do I cite ASReview 5-Star?

```bibtex
@software{asreview_5star,
  title = {ASReview 5-Star: Enhanced Systematic Review Tools},
  author = {ASReview Team},
  year = {2024},
  url = {https://github.com/asreview/asreview-5star}
}
```

---

## Stopping Rules

### Which stopping rule should I use?

| Rule | Best For | Strengths | Limitations |
|------|----------|-----------|-------------|
| **Bayesian** | High-stakes reviews | Formal probability of target recall | Computationally intensive |
| **SPRT** | Known prevalence expectations | Sequential testing framework | Requires prior estimates |
| **SAFE** | Adaptive thresholds | Self-calibrating | Needs at least 1 relevant found |
| **Consecutive** | Simple screening | Easy to understand | May stop too early |

**Recommendation**: Use multiple rules and require consensus (2-3 rules agreeing).

### What is the difference between 95% confidence and 95% recall?

- **95% recall**: You want to find 95% of all relevant documents
- **95% confidence**: You are 95% confident that target recall has been achieved

Example: "95% confident of achieving 95% recall" means there's a 95% probability that you've found at least 95% of all relevant documents.

### Can I stop screening before finding any relevant documents?

**No.** All stopping rules require at least one relevant document to calibrate prevalence estimates. If you've screened extensively without finding relevant documents, this suggests either:

1. The true prevalence is very low
2. Your inclusion criteria may be too strict
3. Your search strategy may need revision

### How many consecutive irrelevant documents should trigger stopping?

This depends on prevalence and dataset size. Common thresholds:

| Prevalence | Recommended Threshold |
|------------|----------------------|
| <1% | 100-200 |
| 1-5% | 50-100 |
| 5-10% | 30-50 |
| >10% | 20-30 |

Use the SAFE rule for adaptive thresholds based on observed prevalence.

---

## Inter-Rater Reliability

### What Kappa value indicates acceptable agreement?

| Kappa Range | Interpretation | Recommendation |
|-------------|----------------|----------------|
| < 0.20 | Poor | Recalibrate immediately |
| 0.20-0.40 | Fair | Recalibrate recommended |
| 0.41-0.60 | Moderate | Acceptable with monitoring |
| 0.61-0.80 | Substantial | Good for most reviews |
| 0.81-1.00 | Almost Perfect | Excellent |

For systematic reviews, aim for Kappa ≥ 0.60 minimum, ≥ 0.80 preferred.

### When should I use Fleiss' Kappa vs Cohen's Kappa?

- **Cohen's Kappa**: Exactly 2 raters
- **Fleiss' Kappa**: 3 or more raters

### What is Krippendorff's Alpha used for?

Krippendorff's Alpha is useful when:

1. You have **missing data** (raters didn't rate all items)
2. You have **ordinal or interval data** (not just binary)
3. You have **variable numbers of raters** per item

### How many records should be in my pilot IRR sample?

Recommendations:

- **Minimum**: 50 records
- **Recommended**: 100-200 records
- **For publication**: 10-20% of total, minimum 100

The sample should include both relevant and irrelevant records in approximate expected proportions.

---

## Meta-Analysis

### Fixed effects vs random effects: which should I use?

| Use Fixed Effects When | Use Random Effects When |
|------------------------|-------------------------|
| Studies are methodologically identical | Studies vary in population, intervention, etc. |
| You want to estimate the common effect | You want to estimate the mean of a distribution |
| Low heterogeneity (I² < 25%) | Moderate to high heterogeneity (I² > 25%) |

**Default recommendation**: Random effects (DerSimonian-Laird) is more conservative and appropriate for most systematic reviews.

### What does I² mean?

I² (I-squared) represents the percentage of variation across studies due to heterogeneity rather than chance:

| I² Value | Interpretation |
|----------|----------------|
| 0-25% | Low heterogeneity |
| 25-50% | Moderate heterogeneity |
| 50-75% | Substantial heterogeneity |
| 75-100% | Considerable heterogeneity |

### How do I interpret publication bias tests?

**Egger's Test**:
- p < 0.10: Suggests possible publication bias
- Uses regression of standardized effects on precision

**Begg's Test**:
- p < 0.10: Suggests possible publication bias
- Uses rank correlation (Kendall's tau)

**Caution**: Both tests have low power with <10 studies. Absence of significant bias doesn't prove bias is absent.

### What effect size measures are supported?

ASReview 5-Star works with any effect size on a continuous scale:

- Log odds ratios
- Log hazard ratios
- Log risk ratios
- Standardized mean differences (Cohen's d, Hedges' g)
- Correlation coefficients (Fisher's z)

Always use the **log-transformed** version for ratios.

---

## PRISMA

### What is PRISMA 2020?

PRISMA 2020 is the updated guideline for reporting systematic reviews. It includes:

- Expanded flow diagram with identification sources
- Separate tracking of database vs. register sources
- Exclusion reasons at full-text stage
- New reporting items for automation

### How do I generate a PRISMA flow diagram?

```python
from asreview_5star import prisma_stats, generate_prisma_svg

stats = prisma_stats(
    records_total=1000,
    records_duplicates=100,
    records_screened=900,
    records_excluded_screening=800,
    records_retrieved=100,
    records_not_retrieved=5,
    records_excluded_fulltext=70
)

svg = generate_prisma_svg(stats)

# Save to file
with open("prisma_flow.svg", "w") as f:
    f.write(svg)
```

### What is yield rate?

Yield rate = (Studies Included / Records Screened) × 100

Example: If you screened 1000 records and included 25 studies, yield rate = 2.5%

Typical yield rates:

| Review Type | Typical Yield |
|-------------|---------------|
| Broad topic | 0.5-2% |
| Focused topic | 2-5% |
| Narrow topic | 5-15% |

---

## Integration

### Can I use ASReview 5-Star with Screenr?

Yes! ASReview 5-Star can integrate with Screenr via:

1. **REST API**: Call ASReview 5-Star API from Screenr
2. **Direct Python**: Import in Python scripts
3. **Export/Import**: Use JSON export from Screenr with Python analysis

### How do I call the REST API from JavaScript?

```javascript
// Example: Calculate stopping probability
const response = await fetch('http://localhost:8000/api/v1/stopping/bayesian', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    n_screened: 500,
    n_relevant: 25,
    n_total: 5000,
    target_recall: 0.95
  })
});

const result = await response.json();
console.log(`Should stop: ${result.should_stop}`);
console.log(`Confidence: ${result.confidence}`);
```

### Can I use ASReview 5-Star in R?

Yes, via the `reticulate` package:

```r
library(reticulate)

# Import ASReview 5-Star
a5s <- import("asreview_5star")

# Use functions
result <- a5s$bayesian_stopping(
  n_screened = 500L,
  n_relevant = 25L,
  n_total = 5000L
)

print(paste("Should stop:", result$should_stop))
```

### How do I run the API server in production?

For production deployment:

```bash
# Using Gunicorn (Linux/Mac)
pip install gunicorn
gunicorn asreview_5star.api.app:app -w 4 -b 0.0.0.0:8000

# Using Docker
docker build -t asreview-5star-api .
docker run -p 8000:8000 asreview-5star-api
```

---

## More Questions?

- **GitHub Issues**: [github.com/asreview/asreview-5star/issues](https://github.com/asreview/asreview-5star/issues)
- **Documentation**: [asreview.nl](https://asreview.nl/)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
