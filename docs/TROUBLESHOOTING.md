# ASReview 5-Star Troubleshooting Guide

This guide helps resolve common issues with ASReview 5-Star.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Import Errors](#import-errors)
- [Stopping Rules](#stopping-rules)
- [IRR Calculations](#irr-calculations)
- [Meta-Analysis](#meta-analysis)
- [PRISMA Statistics](#prisma-statistics)
- [REST API](#rest-api)
- [Performance Issues](#performance-issues)

---

## Installation Issues

### Problem: `pip install` fails with dependency errors

**Solution:**

1. Ensure you have Python 3.8 or higher:
   ```bash
   python --version
   ```

2. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

3. Install with verbose output to identify the failing dependency:
   ```bash
   pip install -v asreview-5star
   ```

4. If scipy fails, install it separately first:
   ```bash
   pip install numpy scipy
   pip install asreview-5star
   ```

### Problem: ImportError after installation

**Solution:**

Check that the package is installed in the correct Python environment:

```python
import sys
print(sys.executable)  # Check which Python is being used

import asreview_5star
print(asreview_5star.__file__)  # Check where it's installed
```

---

## Import Errors

### Problem: `ModuleNotFoundError: No module named 'asreview_5star'`

**Solution:**

1. Verify installation:
   ```bash
   pip show asreview-5star
   ```

2. If using virtual environment, ensure it's activated:
   ```bash
   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. Install in the current environment:
   ```bash
   pip install asreview-5star
   ```

### Problem: `ImportError: cannot import name 'XXX' from 'asreview_5star'`

**Solution:**

1. Check you're using the correct function name:
   ```python
   # List all available exports
   import asreview_5star
   print(dir(asreview_5star))
   ```

2. Update to the latest version:
   ```bash
   pip install --upgrade asreview-5star
   ```

---

## Stopping Rules

### Problem: Bayesian stopping always returns `should_stop=False`

**Possible causes:**

1. **No relevant documents found yet**: The Bayesian method requires at least one relevant document.
   ```python
   # Check your data
   if n_relevant == 0:
       print("Warning: No relevant documents found yet")
   ```

2. **Too few documents screened**: Need sufficient data for reliable estimates.

3. **Target recall too high**: Try lowering target_recall (e.g., 0.90 instead of 0.95).

**Solution:**

```python
result = bayesian_stopping(
    n_screened=n_screened,
    n_relevant=n_relevant,
    n_total=n_total,
    target_recall=0.90,  # Lower target
    confidence_threshold=0.90  # Lower confidence threshold
)
```

### Problem: SPRT returns `decision: continue` indefinitely

**Solution:**

Adjust the prevalence hypotheses to match your data:

```python
# Calculate observed prevalence
observed_prevalence = n_relevant / n_screened

# Set null hypothesis below observed
result = sprt_stopping(
    n_screened=n_screened,
    n_relevant=n_relevant,
    null_prevalence=observed_prevalence * 0.5,  # Below observed
    alt_prevalence=observed_prevalence * 1.5    # Above observed
)
```

---

## IRR Calculations

### Problem: Cohen's Kappa returns 1.0 or NaN

**Causes:**

1. **Perfect agreement**: All ratings match (kappa = 1.0 is correct)
2. **No variance**: One rater always gives the same rating

**Solution:**

Check your data for variability:

```python
import numpy as np

rater1 = [1, 1, 1, 1, 1]  # No variance!
rater2 = [1, 1, 1, 1, 0]

# Add variance check
if len(set(rater1)) == 1 or len(set(rater2)) == 1:
    print("Warning: One rater has no variance")
```

### Problem: Fleiss' Kappa returns negative value

**Explanation:**

Negative kappa indicates agreement worse than chance. This can occur when:

1. Raters systematically disagree
2. Data entry errors (labels reversed)
3. Raters using different criteria

**Solution:**

1. Review disagreements:
   ```python
   # Find disagreements
   for i, row in enumerate(ratings):
       if len(set(row)) > 1:
           print(f"Record {i}: {row}")
   ```

2. Check for label reversals:
   ```python
   # Count each rater's positive rate
   for j in range(len(ratings[0])):
       rater_ratings = [row[j] for row in ratings]
       print(f"Rater {j+1} positive rate: {sum(rater_ratings)/len(rater_ratings):.2%}")
   ```

---

## Meta-Analysis

### Problem: `ValueError: Effects and standard errors must have equal length`

**Solution:**

Verify your data:

```python
effects = [0.5, 0.6, 0.7]
ses = [0.1, 0.2]  # Missing one!

print(f"Effects: {len(effects)}, SEs: {len(ses)}")
# Should be equal
```

### Problem: Heterogeneity statistics show I² = 0%

**Explanation:**

This is correct when:
- Studies are homogeneous
- Only 2-3 studies included
- Effect sizes are very similar

**Solution:**

With limited studies, interpret cautiously:

```python
result = pool_effects(effects, ses, model="random")

if len(effects) < 5:
    print("Warning: Heterogeneity estimates unreliable with <5 studies")
```

### Problem: Publication bias test returns `Insufficient studies`

**Solution:**

Egger's and Begg's tests require at least 3-4 studies:

```python
if len(effects) < 3:
    print("Cannot perform bias tests with fewer than 3 studies")
else:
    egger = eggers_test(effects, ses)
    print(egger.interpretation)
```

---

## PRISMA Statistics

### Problem: Calculated values don't match manual counts

**Solution:**

Verify the PRISMA calculation logic:

```python
# PRISMA calculations
stats = prisma_stats(
    records_total=1000,
    records_duplicates=100,
    records_screened=900,
    records_excluded_screening=800,
    records_retrieved=100,
    records_not_retrieved=5,
    records_excluded_fulltext=70
)

# Manual verification
print(f"Expected screened: {1000 - 100} = 900")
print(f"Actual screened: {stats.records_screened}")

print(f"Expected assessed: {100 - 5} = 95")
print(f"Actual assessed: {stats.reports_assessed}")

print(f"Expected included: {95 - 70} = 25")
print(f"Actual included: {stats.studies_included}")
```

---

## REST API

### Problem: API server won't start

**Solution:**

1. Check if port is in use:
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :8000
   ```

2. Try a different port:
   ```bash
   asreview-5star serve --port 8001
   ```

3. Check for missing dependencies:
   ```bash
   pip install asreview-5star[api]
   ```

### Problem: CORS errors when calling API from browser

**Solution:**

The API allows all origins by default. If issues persist:

```python
from asreview_5star.api import create_app

app = create_app(cors_origins=["http://localhost:3000", "https://yourdomain.com"])
```

### Problem: API returns 422 Validation Error

**Solution:**

Check your request body matches the expected schema:

```python
# Correct format
{
    "n_screened": 500,    # Integer, required
    "n_relevant": 25,     # Integer, required
    "n_total": 5000       # Integer, required
}

# Common mistakes:
# - Strings instead of integers
# - Missing required fields
# - Extra fields not in schema
```

---

## Performance Issues

### Problem: Bayesian stopping is slow with large datasets

**Solution:**

1. Reduce Monte Carlo samples:
   ```python
   # Modify in source or use caching
   # Default is 10000 samples
   ```

2. Use SPRT or consecutive stopping for quick checks:
   ```python
   # SPRT is much faster
   result = sprt_stopping(n_screened, n_relevant)
   ```

### Problem: Meta-analysis with many studies is slow

**Solution:**

1. Use fixed effects for initial analysis:
   ```python
   # Fixed effects is faster than random effects
   result = pool_effects(effects, ses, model="fixed")
   ```

2. Consider pre-computing for repeated analyses:
   ```python
   # Cache results
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def cached_pool(effects_tuple, ses_tuple, model):
       return pool_effects(list(effects_tuple), list(ses_tuple), model=model)
   ```

---

## Getting Help

If you can't resolve your issue:

1. **Check the FAQ**: See [FAQ.md](FAQ.md)
2. **Search GitHub Issues**: [github.com/asreview/asreview-5star/issues](https://github.com/asreview/asreview-5star/issues)
3. **Open a new issue** with:
   - Python version (`python --version`)
   - Package version (`pip show asreview-5star`)
   - Minimal reproducible example
   - Full error traceback
