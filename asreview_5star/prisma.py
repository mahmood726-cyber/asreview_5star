"""
PRISMA Flow Diagram Support

Functions for generating PRISMA 2020 compliant statistics
and flow diagram data.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PRISMAStats:
    """PRISMA flow diagram statistics."""
    # Identification
    records_identified_databases: int
    records_identified_registers: int
    records_identified_other: int
    records_removed_duplicates: int

    # Screening
    records_screened: int
    records_excluded_title_abstract: int

    # Eligibility
    reports_sought: int
    reports_not_retrieved: int
    reports_assessed: int
    reports_excluded: int
    exclusion_reasons: Dict[str, int]

    # Included
    studies_included: int
    reports_included: int


def prisma_stats(
    records_total: int,
    records_duplicates: int,
    records_screened: int,
    records_excluded_screening: int,
    records_retrieved: int,
    records_not_retrieved: int,
    records_excluded_fulltext: int,
    exclusion_reasons: Optional[Dict[str, int]] = None,
    records_from_databases: Optional[int] = None,
    records_from_registers: int = 0,
    records_from_other: int = 0
) -> PRISMAStats:
    """
    Calculate PRISMA flow diagram statistics.

    Parameters
    ----------
    records_total : int
        Total records identified.
    records_duplicates : int
        Records removed as duplicates.
    records_screened : int
        Records screened (title/abstract).
    records_excluded_screening : int
        Records excluded at title/abstract screening.
    records_retrieved : int
        Reports/records sought for retrieval.
    records_not_retrieved : int
        Reports not retrieved.
    records_excluded_fulltext : int
        Reports excluded at full-text review.
    exclusion_reasons : Optional[Dict[str, int]]
        Breakdown of exclusion reasons at full-text.
    records_from_databases : Optional[int]
        Records from database searching (default: all from databases).
    records_from_registers : int
        Records from registers.
    records_from_other : int
        Records from other sources.

    Returns
    -------
    PRISMAStats
        PRISMA 2020 compliant statistics.
    """
    if records_from_databases is None:
        records_from_databases = records_total - records_from_registers - records_from_other

    reports_assessed = records_retrieved - records_not_retrieved
    studies_included = reports_assessed - records_excluded_fulltext

    if exclusion_reasons is None:
        exclusion_reasons = {"Unspecified": records_excluded_fulltext}

    return PRISMAStats(
        records_identified_databases=records_from_databases,
        records_identified_registers=records_from_registers,
        records_identified_other=records_from_other,
        records_removed_duplicates=records_duplicates,
        records_screened=records_screened,
        records_excluded_title_abstract=records_excluded_screening,
        reports_sought=records_retrieved,
        reports_not_retrieved=records_not_retrieved,
        reports_assessed=reports_assessed,
        reports_excluded=records_excluded_fulltext,
        exclusion_reasons=exclusion_reasons,
        studies_included=studies_included,
        reports_included=studies_included  # May differ if multiple reports per study
    )


def prisma_flow_data(stats: PRISMAStats) -> Dict:
    """
    Generate data structure for PRISMA 2020 flow diagram.

    Parameters
    ----------
    stats : PRISMAStats
        PRISMA statistics.

    Returns
    -------
    Dict
        Hierarchical data structure for flow diagram generation.
    """
    total_identified = (
        stats.records_identified_databases +
        stats.records_identified_registers +
        stats.records_identified_other
    )

    return {
        "version": "PRISMA 2020",
        "identification": {
            "databases": {
                "n": stats.records_identified_databases,
                "label": "Records identified from databases"
            },
            "registers": {
                "n": stats.records_identified_registers,
                "label": "Records identified from registers"
            },
            "other": {
                "n": stats.records_identified_other,
                "label": "Records identified from other sources"
            },
            "total": {
                "n": total_identified,
                "label": "Total records identified"
            },
            "duplicates_removed": {
                "n": stats.records_removed_duplicates,
                "label": "Duplicate records removed"
            }
        },
        "screening": {
            "records_screened": {
                "n": stats.records_screened,
                "label": "Records screened"
            },
            "records_excluded": {
                "n": stats.records_excluded_title_abstract,
                "label": "Records excluded"
            }
        },
        "eligibility": {
            "reports_sought": {
                "n": stats.reports_sought,
                "label": "Reports sought for retrieval"
            },
            "reports_not_retrieved": {
                "n": stats.reports_not_retrieved,
                "label": "Reports not retrieved"
            },
            "reports_assessed": {
                "n": stats.reports_assessed,
                "label": "Reports assessed for eligibility"
            },
            "reports_excluded": {
                "n": stats.reports_excluded,
                "label": "Reports excluded",
                "reasons": [
                    {"reason": reason, "n": count}
                    for reason, count in stats.exclusion_reasons.items()
                ]
            }
        },
        "included": {
            "studies": {
                "n": stats.studies_included,
                "label": "Studies included in review"
            },
            "reports": {
                "n": stats.reports_included,
                "label": "Reports of included studies"
            }
        },
        "summary": {
            "identification_total": total_identified,
            "after_duplicates": total_identified - stats.records_removed_duplicates,
            "screened": stats.records_screened,
            "after_screening": stats.records_screened - stats.records_excluded_title_abstract,
            "assessed_fulltext": stats.reports_assessed,
            "final_included": stats.studies_included,
            "yield_rate": (
                stats.studies_included / stats.records_screened * 100
                if stats.records_screened > 0 else 0
            )
        }
    }


def generate_prisma_svg(stats: PRISMAStats, width: int = 800, height: int = 600) -> str:
    """
    Generate SVG representation of PRISMA flow diagram.

    Parameters
    ----------
    stats : PRISMAStats
        PRISMA statistics.
    width : int
        SVG width in pixels.
    height : int
        SVG height in pixels.

    Returns
    -------
    str
        SVG markup string.
    """
    flow_data = prisma_flow_data(stats)

    # Box dimensions
    box_w = 180
    box_h = 60
    margin = 20

    # Colors
    id_color = "#e3f2fd"
    screen_color = "#fff3e0"
    elig_color = "#f3e5f5"
    incl_color = "#e8f5e9"
    excl_color = "#ffebee"
    border_color = "#333"

    # SVG header
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="font-family: Arial, sans-serif; font-size: 12px;">
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="{border_color}" />
        </marker>
    </defs>
'''

    # Helper function to create boxes
    def box(x, y, w, h, text, count, fill):
        return f'''<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{border_color}" stroke-width="1.5" rx="4"/>
        <text x="{x + w/2}" y="{y + h/2 - 8}" text-anchor="middle" font-size="11">{text}</text>
        <text x="{x + w/2}" y="{y + h/2 + 10}" text-anchor="middle" font-weight="bold" font-size="14">(n = {count})</text>'''

    # Helper for arrows
    def arrow(x1, y1, x2, y2):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{border_color}" stroke-width="1.5" marker-end="url(#arrowhead)"/>'

    # Calculate positions
    col1 = 50
    col2 = col1 + box_w + margin
    col3 = col2 + box_w + margin

    row1 = 30
    row2 = row1 + box_h + 40
    row3 = row2 + box_h + 40
    row4 = row3 + box_h + 40
    row5 = row4 + box_h + 40

    # Identification section
    svg += box(col1, row1, box_w, box_h, "Records from databases", stats.records_identified_databases, id_color)
    svg += box(col3, row1, box_w, box_h, "Duplicates removed", stats.records_removed_duplicates, excl_color)

    # Screening section
    total_after_dup = (stats.records_identified_databases + stats.records_identified_registers +
                       stats.records_identified_other - stats.records_removed_duplicates)
    svg += box(col1, row2, box_w, box_h, "Records screened", stats.records_screened, screen_color)
    svg += box(col3, row2, box_w, box_h, "Records excluded", stats.records_excluded_title_abstract, excl_color)

    # Eligibility section
    svg += box(col1, row3, box_w, box_h, "Reports sought", stats.reports_sought, elig_color)
    svg += box(col3, row3, box_w, box_h, "Not retrieved", stats.reports_not_retrieved, excl_color)

    svg += box(col1, row4, box_w, box_h, "Reports assessed", stats.reports_assessed, elig_color)
    svg += box(col3, row4, box_w, box_h, "Reports excluded", stats.reports_excluded, excl_color)

    # Included section
    svg += box(col1, row5, box_w, box_h, "Studies included", stats.studies_included, incl_color)

    # Arrows
    svg += arrow(col1 + box_w/2, row1 + box_h, col1 + box_w/2, row2)
    svg += arrow(col1 + box_w, row1 + box_h/2, col3, row1 + box_h/2)
    svg += arrow(col1 + box_w/2, row2 + box_h, col1 + box_w/2, row3)
    svg += arrow(col1 + box_w, row2 + box_h/2, col3, row2 + box_h/2)
    svg += arrow(col1 + box_w/2, row3 + box_h, col1 + box_w/2, row4)
    svg += arrow(col1 + box_w, row3 + box_h/2, col3, row3 + box_h/2)
    svg += arrow(col1 + box_w/2, row4 + box_h, col1 + box_w/2, row5)
    svg += arrow(col1 + box_w, row4 + box_h/2, col3, row4 + box_h/2)

    svg += '</svg>'
    return svg
