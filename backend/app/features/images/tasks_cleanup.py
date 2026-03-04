"""
Image Tasks - Analysis Text Cleanup.

Strips structural STEP headers, separator lines, and instruction sections
from AI analysis output, keeping only the descriptive content.

Safety: metadata extraction (tags, wikilinks, content_type) happens BEFORE
this cleanup runs, so all structured data is already captured.
"""

import re


def clean_analysis_text(raw: str) -> str:
    """
    Strip structural prompt artifacts from AI analysis text.

    Removes:
    - Separator lines (═══════, -------, etc.)
    - STEP N: HEADER lines (plain, bold, or markdown heading variants)
    - Content Type: X line (already extracted as metadata)
    - STEP 4 / SEARCHABLE ELEMENTS section entirely
    - CRITICAL INSTRUCTIONS section
    - OUTPUT FORMAT section
    - Trailing Tags: #foo #bar lines

    Keeps:
    - Actual description from STEP 2
    - Key observations from STEP 3

    Args:
        raw: Raw AI analysis text

    Returns:
        Cleaned text with only descriptive content
    """
    if not raw:
        return raw

    lines = raw.split("\n")
    cleaned = []
    skip_section = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines while in a skip section
        if skip_section and stripped == "":
            continue

        # Skip separator lines (═══, ───, ---, ***, etc.)
        if re.match(r'^[\s*═=─\-~_]{5,}$', stripped):
            continue

        # Skip STEP N: HEADER lines (plain, bold, or heading variants)
        # Handles: "STEP 1:", "**STEP 2:**", "## STEP 3:", "### STEP 4."
        step_match = re.match(
            r'^(?:\*{1,2})?(?:#+\s*)?STEP\s+(\d+)\s*[:.]\s*.*?(?:\*{1,2})?$',
            stripped,
            re.IGNORECASE,
        )
        if step_match:
            step_num = int(step_match.group(1))
            # STEP 4+ (searchable elements) - skip entire section
            if step_num >= 4:
                skip_section = True
            continue

        # Skip Content Type: X line
        if re.match(
            r'^(?:\*{1,2})?Content\s+Type\s*(?:\*{1,2})?\s*:\s*\w',
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip CRITICAL INSTRUCTIONS / OUTPUT FORMAT sections
        if re.match(
            r'^(?:\*{1,2})?(?:CRITICAL\s+INSTRUCTIONS|OUTPUT\s+FORMAT)'
            r'\s*(?:\*{1,2})?\s*:',
            stripped,
            re.IGNORECASE,
        ):
            skip_section = True
            continue

        # Skip SEARCHABLE ELEMENTS header variant
        if re.match(
            r'^(?:\*{1,2})?(?:#+\s*)?SEARCHABLE\s+ELEMENTS',
            stripped,
            re.IGNORECASE,
        ):
            skip_section = True
            continue

        # Skip KEY OBSERVATIONS header if standalone (without STEP prefix)
        if re.match(
            r'^(?:\*{1,2})?(?:#+\s*)?KEY\s+OBSERVATIONS\s*(?:\*{1,2})?:?\s*$',
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip DESCRIBE WHAT YOU SEE header if standalone
        if re.match(
            r'^(?:\*{1,2})?(?:#+\s*)?DESCRIBE\s+WHAT\s+YOU\s+SEE'
            r'\s*(?:\*{1,2})?:?\s*$',
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip IDENTIFY CONTENT TYPE header if standalone
        if re.match(
            r'^(?:\*{1,2})?(?:#+\s*)?IDENTIFY\s+CONTENT\s+TYPE'
            r'\s*(?:\*{1,2})?:?\s*$',
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Detect end of a skipped section: a new STEP or substantial content
        if skip_section:
            # A new STEP N header ends skip (the STEP line itself is handled above)
            if re.match(r'^(?:\*{1,2})?(?:#+\s*)?STEP\s+\d+', stripped, re.IGNORECASE):
                skip_section = False
                continue
            # Otherwise keep skipping
            continue

        # Skip trailing Tags: #foo #bar lines
        if re.match(
            r'^(?:\*{1,2})?Tags?\s*(?:\*{1,2})?\s*:',
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip "Begin now with your analysis" prompt leak
        if re.match(
            r'^Begin\s+now\s+with\s+your\s+analysis',
            stripped,
            re.IGNORECASE,
        ):
            continue

        cleaned.append(line)

    # Join and collapse excessive blank lines
    result = "\n".join(cleaned)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()
