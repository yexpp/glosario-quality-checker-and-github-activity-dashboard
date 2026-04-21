#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from collections import defaultdict
from functools import partial

from glossary_checker import (
    get_glossary_yml_content,
    load_yaml,
    get_slug_line_map,
    format_line_info,
    validate_glossary,
    check_cross_language_links,
    check_slug_order,
    check_language_order,
    check_ref_validity,
    check_def_not_empty,
    check_def_style,
)

# Dictionary to store logs categorized by check name
LOGS = defaultdict(list)


def info(msg, *args, check_name=None):
    text = msg % args if args else msg
    print(f"::notice::{text}", file=sys.stderr)
    if check_name:
        LOGS[check_name].append(("INFO", text))
        

def warning(msg, *args, check_name=None):
    text = msg % args if args else msg
    print(f"::warning::{text}", file=sys.stderr)
    if check_name:
        LOGS[check_name].append(("WARNING", text))
        
        
def error(msg, *args, check_name=None):
    text = msg % args if args else msg
    print(f"::error::{text}", file=sys.stderr)
    if check_name:
        LOGS[check_name].append(("ERROR", text))

        
def load_glossary():
    """
    Load glossary content from YAML file.

    Returns:
        dict: Parsed glossary data.

    Raises:
        ValueError: If glossary content is empty or parsing fails.
    """
    glossary_str = get_glossary_yml_content()
    if not glossary_str:
        raise ValueError("Glossary content is empty")

    glossary = load_yaml(glossary_str)
    if not glossary:
        raise ValueError("Parsed glossary is empty")

    info("Loaded glossary with %s entries.", len(glossary))
    return glossary


def load_language_codes(json_path: Path):
    """
    Load language codes from a JSON file.
    
    Args:
        json_path: Path to the language codes JSON file.
        
    Returns:
        Dictionary mapping language codes to language names.
    """
    if not json_path.is_file():
        error("Language codes file not found: %s", json_path)
        return {}
    try:
        with json_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        error("Failed to load language codes: %s", e)
        return {}
    

def report_basic_format(glossary, slug_lines, check_name="Basic Format Validation"):
    """
    Validate basic glossary structure and formatting.
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        check_name: Name of the validation check for logging.
        
    Returns:
        True if issues found, else False.
    """
    issues = validate_glossary(glossary, slug_lines=slug_lines)
    if issues:
        warning("Found basic format issues:", check_name=check_name)
        for issue in issues:
            warning("  - %s", issue, check_name=check_name)
        return True
    info("All entries comply with basic structure specifications!", check_name=check_name)
    return False


def report_ref_validity(glossary, slug_lines, check_name="Reference validity check"):
    """
    Check if all 'ref' entries point to existing slugs.
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        check_name: Name of the validation check for logging.
        
    Returns:
        True if issues found, else False.
    """
    issues = check_ref_validity(glossary, slug_lines=slug_lines)
    if issues:
        warning("Issues found with refs:", check_name=check_name)
        for issue in issues:
            warning("  - %s", issue, check_name=check_name)
        return True
    info("All refs reference valid slugs.", check_name=check_name)
    return False


def report_cross_links(glossary, slug_lines, language_names, check_name="Reference Consistency Check"):
    """
    Verify cross-language reference links are consistent.
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        language_names: Dict of language code to language name.
        check_name: Name of the validation check for logging.
        
    Returns:
        True if missing links found, else False.
    """
    issues = check_cross_language_links(glossary, slug_lines)
    if not issues:
        info("All cross-reference links are consistent across languages.", check_name=check_name)
        return False

    grouped = defaultdict(list)
    for issue in issues:
        line = slug_lines.get(issue["slug"]) if slug_lines else None
        key = (issue["slug"], line, issue["missing_link"])
        grouped[key].append(issue["lang"])

    # Organize missing links by language
    lang_dict = defaultdict(list)
    for (slug, line, missing_link), langs in grouped.items():
        for lang in langs:
            lang_dict[lang].append((slug, line, missing_link))

    warning("Missing cross-reference links found (grouped by language):", check_name=check_name)
    for lang_code in sorted(lang_dict.keys()):
        lang_name = language_names.get(lang_code, lang_code)
        warning("  %s:", lang_name, check_name=check_name)
        for slug, line, missing_link in sorted(lang_dict[lang_code], key=lambda x: (x[0], x[1] or 0)):
            line_info = f"line {line}" if line else ""
            warning("    - slug '%s' (%s) missing link #%s", slug, line_info, missing_link, check_name=check_name)
    return True


def report_slug_order(glossary, slug_lines, check_name="Slug Order Check"):
    """
    Check that glossary entries are sorted alphabetically by slug.
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        check_name: Name of the validation check for logging.
        
    Returns:
        True if sorting issues found, else False.
    """
    issues = check_slug_order(glossary, slug_lines=slug_lines)
    if issues:
        warning("Entries are not sorted in slug alphabetical order:", check_name=check_name)
        for issue in issues:
            warning("  - %s", issue, check_name=check_name)
        return True
    info("Entries are sorted in slug alphabetical order.", check_name=check_name)
    return False


def report_language_order(glossary, slug_lines, check_name="Language Code Order Check"):
    """
    Check language code order in each entry is valid.
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        check_name: Name of the validation check for logging.
        
    Returns:
        True if ordering issues found, else False.
    """
    issues = check_language_order(glossary, slug_lines=slug_lines)
    if issues:
        warning("Entries with incorrect language code order:", check_name=check_name)
        for issue in issues:
            warning("  - %s", issue, check_name=check_name)
        return True
    info("Language codes in all entries are sorted alphabetically.", check_name=check_name)
    return False


def report_empty_defs(glossary, slug_lines, check_name="Definition Fields Non-empty check"):
    """
    Check that 'def' fields are not empty.
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        check_name: Name of the validation check for logging.
        
    Returns:
        True if empty definitions found, else False.
    """
    issues = check_def_not_empty(glossary, slug_lines=slug_lines)
    if issues:
        warning("Issues found with def fields:", check_name=check_name)
        for issue in issues:
            warning("  - %s", issue, check_name=check_name)
        return True
    info("All def fields are non-empty.", check_name=check_name)
    return False


def report_style(glossary, slug_lines, style_marker=">", check_name="Definition Fields Format check"):
    """
    Validate YAML style of 'def' fields (e.g., folded style).
    
    Args:
        glossary: Glossary data.
        slug_lines: Mapping of slugs to line info.
        style_marker: YAML style marker to check for (default '>').
        check_name: Name of the validation check for logging.
        
    Returns:
        True if style issues found, else False.
    """
    issues = check_def_style(glossary, style_marker, slug_lines=slug_lines)
    if issues:
        warning("YAML style issues found in def fields:", check_name=check_name)
        for issue in issues:
            warning("  - %s", issue, check_name=check_name)
        return True
    info("All def fields use the correct YAML folded style.", check_name=check_name)
    return False


def run_glossary_check(language_codes_path="language-codes.json"):
    """
    Execute all glossary validation checks and collect results.
    
    Args:
        language_codes_path: Path to the language codes JSON file.
        
    Returns:
        Dictionary containing overall success status, individual check results, and logs.
    """
    LOGS.clear()
    glossary = load_glossary()
    if glossary is None:
        return {"success": False, "results": [], "logs": LOGS}

    slug_lines = get_slug_line_map(glossary)
    language_names = load_language_codes(Path(language_codes_path))

    checks = [
        ("Basic Format Validation", report_basic_format),
        ("Reference validity check", report_ref_validity),
        ("Reference Consistency Check", partial(report_cross_links, language_names=language_names)),
        ("Slug Order Check", report_slug_order),
        ("Language Code Order Check", report_language_order),
        ("Definition Fields Format check", partial(report_style, style_marker=">")),
        ("Definition Fields Non-empty check", report_empty_defs),
    ]

    results = []
    has_issues = False
    for name, func in checks:
        issue = func(glossary, slug_lines, check_name=name)
        has_issues |= issue
        results.append((name, "⚠️ Issue found" if issue else "✅ Passed"))

    return {"success": not has_issues, "results": results, "logs": LOGS}


if __name__ == "__main__":
    result = run_glossary_check()

    output_path = "report.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Report saved to {output_path}")

    sys.exit(1 if result.get("errors") else 0)
