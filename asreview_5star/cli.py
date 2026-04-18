"""
Command Line Interface for ASReview 5-Star.

Provides commands for:
- Running the REST API server
- Calculating stopping rules
- Computing IRR statistics
- Performing meta-analysis
"""

import argparse
import json
import sys
from typing import Optional


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="asreview-5star",
        description="ASReview 5-Star: Enhanced Systematic Review Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  asreview-5star serve                    # Start API server
  asreview-5star serve --port 8080        # Start on custom port
  asreview-5star stopping --help          # Stopping rules help
  asreview-5star irr --help               # IRR calculations help
  asreview-5star meta --help              # Meta-analysis help
"""
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # =========================================================
    # Serve command
    # =========================================================
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the REST API server"
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    # =========================================================
    # Stopping command
    # =========================================================
    stopping_parser = subparsers.add_parser(
        "stopping",
        help="Calculate stopping rule probabilities"
    )
    stopping_parser.add_argument(
        "--method",
        choices=["bayesian", "sprt", "safe", "consecutive"],
        default="bayesian",
        help="Stopping method (default: bayesian)"
    )
    stopping_parser.add_argument(
        "--screened",
        type=int,
        required=True,
        help="Number of documents screened"
    )
    stopping_parser.add_argument(
        "--relevant",
        type=int,
        required=True,
        help="Number of relevant documents found"
    )
    stopping_parser.add_argument(
        "--total",
        type=int,
        required=True,
        help="Total number of documents"
    )
    stopping_parser.add_argument(
        "--consecutive",
        type=int,
        default=0,
        help="Consecutive irrelevant count (for safe/consecutive methods)"
    )
    stopping_parser.add_argument(
        "--target-recall",
        type=float,
        default=0.95,
        help="Target recall level (default: 0.95)"
    )
    stopping_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    # =========================================================
    # IRR command
    # =========================================================
    irr_parser = subparsers.add_parser(
        "irr",
        help="Calculate inter-rater reliability"
    )
    irr_parser.add_argument(
        "--method",
        choices=["kappa", "fleiss", "krippendorff", "percent"],
        default="kappa",
        help="IRR method (default: kappa)"
    )
    irr_parser.add_argument(
        "--file",
        required=True,
        help="CSV file with ratings (columns: subject, rater1, rater2, ...)"
    )
    irr_parser.add_argument(
        "--weights",
        choices=["none", "linear", "quadratic"],
        default="none",
        help="Weighting for kappa (default: none)"
    )
    irr_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    # =========================================================
    # Meta command
    # =========================================================
    meta_parser = subparsers.add_parser(
        "meta",
        help="Perform meta-analysis"
    )
    meta_parser.add_argument(
        "--file",
        required=True,
        help="CSV file with study data (columns: name, effect, se)"
    )
    meta_parser.add_argument(
        "--model",
        choices=["fixed", "random"],
        default="random",
        help="Meta-analysis model (default: random)"
    )
    meta_parser.add_argument(
        "--bias-test",
        action="store_true",
        help="Include publication bias tests"
    )
    meta_parser.add_argument(
        "--exponentiate",
        action="store_true",
        help="Exponentiate effects (for log-transformed data)"
    )
    meta_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    # =========================================================
    # PRISMA command
    # =========================================================
    prisma_parser = subparsers.add_parser(
        "prisma",
        help="Generate PRISMA statistics"
    )
    prisma_parser.add_argument(
        "--total",
        type=int,
        required=True,
        help="Total records identified"
    )
    prisma_parser.add_argument(
        "--duplicates",
        type=int,
        required=True,
        help="Duplicates removed"
    )
    prisma_parser.add_argument(
        "--screened",
        type=int,
        required=True,
        help="Records screened"
    )
    prisma_parser.add_argument(
        "--excluded-screening",
        type=int,
        required=True,
        help="Excluded at screening"
    )
    prisma_parser.add_argument(
        "--retrieved",
        type=int,
        required=True,
        help="Full-text retrieved"
    )
    prisma_parser.add_argument(
        "--not-retrieved",
        type=int,
        default=0,
        help="Full-text not retrieved"
    )
    prisma_parser.add_argument(
        "--excluded-fulltext",
        type=int,
        required=True,
        help="Excluded at full-text"
    )
    prisma_parser.add_argument(
        "--svg",
        action="store_true",
        help="Generate SVG flow diagram"
    )
    prisma_parser.add_argument(
        "--output",
        help="Output file path"
    )
    prisma_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Execute commands
    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "stopping":
        cmd_stopping(args)
    elif args.command == "irr":
        cmd_irr(args)
    elif args.command == "meta":
        cmd_meta(args)
    elif args.command == "prisma":
        cmd_prisma(args)


def cmd_serve(args):
    """Run the API server."""
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required. Install with: pip install uvicorn")
        sys.exit(1)

    print(f"Starting ASReview 5-Star API server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        "asreview_5star.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


def cmd_stopping(args):
    """Calculate stopping rule."""
    from .stopping import (
        bayesian_stopping,
        sprt_stopping,
        safe_stopping,
        consecutive_irrelevant_stopping
    )

    if args.method == "bayesian":
        result = bayesian_stopping(
            n_screened=args.screened,
            n_relevant=args.relevant,
            n_total=args.total,
            target_recall=args.target_recall
        )
    elif args.method == "sprt":
        result = sprt_stopping(
            n_screened=args.screened,
            n_relevant=args.relevant
        )
    elif args.method == "safe":
        result = safe_stopping(
            n_screened=args.screened,
            n_relevant=args.relevant,
            consecutive_irrelevant=args.consecutive,
            n_total=args.total,
            target_recall=args.target_recall
        )
    elif args.method == "consecutive":
        result = consecutive_irrelevant_stopping(
            consecutive_count=args.consecutive,
            n_relevant=args.relevant
        )

    if args.json:
        output = {
            "should_stop": result.should_stop,
            "confidence": result.confidence,
            "message": result.message,
            "details": result.details
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"Stopping Rule: {args.method.upper()}")
        print(f"{'='*50}")
        print(f"Should Stop: {'YES' if result.should_stop else 'NO'}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Message: {result.message}")
        print(f"{'='*50}\n")


def cmd_irr(args):
    """Calculate IRR statistics."""
    import csv
    from .irr import cohens_kappa, fleiss_kappa, krippendorff_alpha, percent_agreement

    # Read data from file
    with open(args.file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if len(rows) == 0:
        print("Error: File is empty")
        sys.exit(1)

    # Extract ratings based on method
    if args.method == "kappa":
        rater1 = [int(r.get('rater1', r.get('Rater1', 0))) for r in rows]
        rater2 = [int(r.get('rater2', r.get('Rater2', 0))) for r in rows]
        weights = None if args.weights == "none" else args.weights
        result = cohens_kappa(rater1, rater2, weights=weights)
    elif args.method == "fleiss":
        # Assume columns are rater1, rater2, rater3, etc.
        rater_cols = [k for k in rows[0].keys() if k.lower().startswith('rater')]
        ratings = [[int(r[col]) for col in rater_cols] for r in rows]
        result = fleiss_kappa(ratings)
    elif args.method == "krippendorff":
        rater_cols = [k for k in rows[0].keys() if k.lower().startswith('rater')]
        data = [[float(r[col]) if r[col] else float('nan') for r in rows] for col in rater_cols]
        result = krippendorff_alpha(data)
    elif args.method == "percent":
        rater1 = [int(r.get('rater1', r.get('Rater1', 0))) for r in rows]
        rater2 = [int(r.get('rater2', r.get('Rater2', 0))) for r in rows]
        result = percent_agreement(rater1, rater2)

    if args.json:
        output = {
            "coefficient": result.coefficient,
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "se": result.se,
            "interpretation": result.interpretation,
            "p_value": result.p_value,
            "details": result.details
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"Inter-Rater Reliability: {args.method.upper()}")
        print(f"{'='*50}")
        print(f"Coefficient: {result.coefficient:.4f}")
        print(f"95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")
        print(f"Standard Error: {result.se:.4f}")
        print(f"Interpretation: {result.interpretation}")
        if result.p_value is not None:
            print(f"P-value: {result.p_value:.4f}")
        print(f"{'='*50}\n")


def cmd_meta(args):
    """Perform meta-analysis."""
    import csv
    from .meta_analysis import pool_effects, eggers_test, beggs_test

    # Read data from file
    with open(args.file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if len(rows) == 0:
        print("Error: File is empty")
        sys.exit(1)

    effects = [float(r.get('effect', r.get('Effect', 0))) for r in rows]
    ses = [float(r.get('se', r.get('SE', r.get('standard_error', 0)))) for r in rows]
    names = [r.get('name', r.get('Name', r.get('study', f'Study {i+1}'))) for i, r in enumerate(rows)]

    result = pool_effects(effects, ses, study_names=names, model=args.model)

    if args.json:
        output = {
            "pooled_effect": result.pooled_effect,
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "se": result.se,
            "p_value": result.p_value,
            "z_score": result.z_score,
            "model": result.model,
            "heterogeneity": result.heterogeneity,
            "studies": result.studies
        }
        if args.bias_test:
            egger = eggers_test(effects, ses)
            begg = beggs_test(effects, ses)
            output["bias_tests"] = {
                "eggers": {
                    "test_statistic": egger.test_statistic,
                    "p_value": egger.p_value,
                    "interpretation": egger.interpretation
                },
                "beggs": {
                    "test_statistic": begg.test_statistic,
                    "p_value": begg.p_value,
                    "interpretation": begg.interpretation
                }
            }
        print(json.dumps(output, indent=2))
    else:
        import math
        print(f"\n{'='*60}")
        print(f"Meta-Analysis Results ({result.model.upper()} Effects)")
        print(f"{'='*60}")

        pooled = result.pooled_effect
        if args.exponentiate:
            pooled = math.exp(pooled)
            ci_l = math.exp(result.ci_lower)
            ci_u = math.exp(result.ci_upper)
            print(f"Pooled Effect (exp): {pooled:.4f}")
            print(f"95% CI (exp): [{ci_l:.4f}, {ci_u:.4f}]")
        else:
            print(f"Pooled Effect: {pooled:.4f}")
            print(f"95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")

        print(f"P-value: {result.p_value:.4f}")
        print(f"Z-score: {result.z_score:.4f}")

        print(f"\nHeterogeneity:")
        print(f"  Q = {result.heterogeneity['Q']:.2f} (p = {result.heterogeneity['Q_p_value']:.4f})")
        print(f"  I² = {result.heterogeneity['I_squared']:.1f}%")
        print(f"  τ² = {result.heterogeneity['tau_squared']:.4f}")

        if args.bias_test:
            egger = eggers_test(effects, ses)
            begg = beggs_test(effects, ses)
            print(f"\nPublication Bias Tests:")
            print(f"  Egger's test: p = {egger.p_value:.4f} - {egger.interpretation}")
            print(f"  Begg's test: p = {begg.p_value:.4f} - {begg.interpretation}")

        print(f"{'='*60}\n")


def cmd_prisma(args):
    """Generate PRISMA statistics."""
    from .prisma import prisma_stats, prisma_flow_data, generate_prisma_svg

    stats = prisma_stats(
        records_total=args.total,
        records_duplicates=args.duplicates,
        records_screened=args.screened,
        records_excluded_screening=args.excluded_screening,
        records_retrieved=args.retrieved,
        records_not_retrieved=args.not_retrieved,
        records_excluded_fulltext=args.excluded_fulltext
    )

    if args.svg:
        svg = generate_prisma_svg(stats)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(svg)
            print(f"SVG saved to {args.output}")
        else:
            print(svg)
    elif args.json:
        flow_data = prisma_flow_data(stats)
        print(json.dumps(flow_data, indent=2))
    else:
        print(f"\n{'='*50}")
        print("PRISMA Flow Statistics")
        print(f"{'='*50}")
        print(f"Identification:")
        print(f"  Records from databases: {stats.records_identified_databases}")
        print(f"  Records from registers: {stats.records_identified_registers}")
        print(f"  Records from other: {stats.records_identified_other}")
        print(f"  Duplicates removed: {stats.records_removed_duplicates}")
        print(f"\nScreening:")
        print(f"  Records screened: {stats.records_screened}")
        print(f"  Records excluded: {stats.records_excluded_screening}")
        print(f"\nEligibility:")
        print(f"  Reports retrieved: {stats.reports_retrieved}")
        print(f"  Reports not retrieved: {stats.reports_not_retrieved}")
        print(f"  Reports assessed: {stats.reports_assessed}")
        print(f"  Reports excluded: {stats.reports_excluded}")
        print(f"\nIncluded:")
        print(f"  Studies included: {stats.studies_included}")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
