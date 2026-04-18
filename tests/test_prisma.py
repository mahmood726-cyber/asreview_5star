"""Tests for PRISMA module."""

import pytest
from asreview_5star.prisma import (
    prisma_stats,
    prisma_flow_data,
    generate_prisma_svg,
    PRISMAStats
)


class TestPRISMAStats:
    """Tests for PRISMA statistics calculation."""

    def test_basic_stats(self):
        """Test basic PRISMA statistics calculation."""
        stats = prisma_stats(
            records_total=1500,
            records_duplicates=300,
            records_screened=1200,
            records_excluded_screening=1050,
            records_retrieved=150,
            records_not_retrieved=10,
            records_excluded_fulltext=90
        )
        assert isinstance(stats, PRISMAStats)
        assert stats.records_identified_databases == 1500
        assert stats.records_removed_duplicates == 300
        assert stats.studies_included == 50

    def test_with_sources(self):
        """Test with different record sources."""
        stats = prisma_stats(
            records_total=1500,
            records_duplicates=300,
            records_screened=1200,
            records_excluded_screening=1050,
            records_retrieved=150,
            records_not_retrieved=10,
            records_excluded_fulltext=90,
            records_from_databases=1200,
            records_from_registers=200,
            records_from_other=100
        )
        assert stats.records_identified_databases == 1200
        assert stats.records_identified_registers == 200
        assert stats.records_identified_other == 100

    def test_exclusion_reasons(self):
        """Test exclusion reasons breakdown."""
        reasons = {
            "Wrong population": 30,
            "Wrong intervention": 25,
            "Wrong outcome": 20,
            "Wrong study design": 15
        }
        stats = prisma_stats(
            records_total=1500,
            records_duplicates=300,
            records_screened=1200,
            records_excluded_screening=1050,
            records_retrieved=150,
            records_not_retrieved=10,
            records_excluded_fulltext=90,
            exclusion_reasons=reasons
        )
        assert stats.exclusion_reasons == reasons

    def test_calculations(self):
        """Test intermediate calculations are correct."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75
        )
        # reports_assessed = 100 - 5 = 95
        # studies_included = 95 - 75 = 20
        assert stats.reports_assessed == 95
        assert stats.studies_included == 20


class TestPRISMAFlowData:
    """Tests for PRISMA flow data generation."""

    def test_flow_data_structure(self):
        """Test flow data has correct structure."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75
        )
        flow_data = prisma_flow_data(stats)

        assert "identification" in flow_data
        assert "screening" in flow_data
        assert "eligibility" in flow_data
        assert "included" in flow_data
        assert "summary" in flow_data

    def test_identification_section(self):
        """Test identification section."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75
        )
        flow_data = prisma_flow_data(stats)
        ident = flow_data["identification"]

        assert "databases" in ident
        assert "registers" in ident
        assert "duplicates_removed" in ident
        assert ident["duplicates_removed"]["n"] == 100

    def test_summary_calculations(self):
        """Test summary calculations."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75
        )
        flow_data = prisma_flow_data(stats)
        summary = flow_data["summary"]

        assert summary["identification_total"] == 1000
        assert summary["after_duplicates"] == 900
        assert summary["final_included"] == 20

    def test_yield_rate(self):
        """Test yield rate calculation."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=1000,  # Use total for simplicity
            records_excluded_screening=900,
            records_retrieved=100,
            records_not_retrieved=0,
            records_excluded_fulltext=50
        )
        flow_data = prisma_flow_data(stats)
        # 50 included / 1000 screened = 5%
        assert flow_data["summary"]["yield_rate"] == 5.0

    def test_exclusion_reasons_in_flow(self):
        """Test exclusion reasons appear in flow data."""
        reasons = {"Wrong design": 50, "Wrong population": 25}
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75,
            exclusion_reasons=reasons
        )
        flow_data = prisma_flow_data(stats)
        reasons_list = flow_data["eligibility"]["reports_excluded"]["reasons"]

        assert len(reasons_list) == 2
        assert any(r["reason"] == "Wrong design" for r in reasons_list)


class TestGeneratePRISMASVG:
    """Tests for PRISMA SVG generation."""

    def test_svg_generation(self):
        """Test SVG is generated."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75
        )
        svg = generate_prisma_svg(stats)

        assert isinstance(svg, str)
        assert svg.startswith("<svg")
        assert "</svg>" in svg

    def test_svg_contains_numbers(self):
        """Test SVG contains the correct numbers."""
        stats = prisma_stats(
            records_total=1500,
            records_duplicates=300,
            records_screened=1200,
            records_excluded_screening=1050,
            records_retrieved=150,
            records_not_retrieved=10,
            records_excluded_fulltext=90
        )
        svg = generate_prisma_svg(stats)

        assert "n = 1500" in svg  # Total from databases
        assert "n = 300" in svg  # Duplicates
        assert "n = 50" in svg  # Included (150 - 10 - 90)

    def test_svg_custom_dimensions(self):
        """Test SVG with custom dimensions."""
        stats = prisma_stats(
            records_total=1000,
            records_duplicates=100,
            records_screened=900,
            records_excluded_screening=800,
            records_retrieved=100,
            records_not_retrieved=5,
            records_excluded_fulltext=75
        )
        svg = generate_prisma_svg(stats, width=1000, height=800)

        assert 'viewBox="0 0 1000 800"' in svg
