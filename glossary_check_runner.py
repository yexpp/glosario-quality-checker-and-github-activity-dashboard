#!/usr/bin/env python3
import argparse
import json
import sys
import traceback
from collections import defaultdict
from pathlib import Path

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


def info(msg, *args):
    print(f"[INFO] {msg % args if args else msg}")


def warning(msg, *args):
    print(f"[WARNING] {msg % args if args else msg}", file=sys.stderr)


def error(msg, *args):
    print(f"[ERROR] {msg % args if args else msg}", file=sys.stderr)


def exception(msg, *args):
    print(f"[ERROR] {msg % args if args else msg}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)


def load_glossary():
    try:
        glossary_str = get_glossary_yml_content()
        if not glossary_str:
            error("Failed to load glossary content (empty string).")
            return None

        glossary = load_yaml(glossary_str)
        if not glossary:
            error("Glossary YAML content is empty or invalid.")
            return None

        info("Loaded glossary with %s entries.", len(glossary))
        return glossary
    except Exception as e:
        exception(f"Error loading glossary: {e}")
        return None


def load_language_codes(json_path: Path):
    if not json_path.is_file():
        error("Language codes file not found: %s", json_path)
        return {}
    try:
        with json_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        exception("Failed to load language codes: %s", e)
        return {}


def report_basic_format(glossary, slug_lines):
    issues = validate_glossary(glossary, slug_lines=slug_lines)
    if issues:
        warning("Found basic format issues:")
        for issue in issues:
            warning("  - %s", issue)
        return True
    else:
        info("All entries comply with basic structure specifications!")
        return False


def report_ref_validity(glossary, slug_lines):
    issues = check_ref_validity(glossary, slug_lines=slug_lines)
    if issues:
        warning("Issues found with refs:")
        for issue in issues:
            warning("  - %s", issue)
        return True
    else:
        info("All refs reference valid slugs.")
        return False


def report_cross_links(glossary, slug_lines, language_names):
    issues = check_cross_language_links(glossary, slug_lines)
    if not issues:
        info("All cross-reference links are consistent across languages.")
        return False

    # Group by (slug, line, missing_link) -> langs
    grouped = defaultdict(list)
    for issue in issues:
        line = slug_lines.get(issue["slug"]) if slug_lines else None
        key = (issue["slug"], line, issue["missing_link"])
        grouped[key].append(issue["lang"])

    lang_dict = defaultdict(list)
    for (slug, line, missing_link), langs in grouped.items():
        for lang in langs:
            lang_dict[lang].append((slug, line, missing_link))

    warning("Missing cross-reference links found (grouped by language):")
    for lang_code in sorted(lang_dict.keys()):
        lang_name = language_names.get(lang_code, lang_code)
        warning("  %s:", lang_name)
        for slug, line, missing_link in sorted(
            lang_dict[lang_code], key=lambda x: (x[0], x[1] or 0)
        ):
            line_info = f"line {line}" if line else ""
            warning(
                "    - slug '%s' (%s) missing link #%s",
                slug,
                line_info,
                missing_link,
            )
    return True


def report_slug_order(glossary, slug_lines):
    issues = check_slug_order(glossary, slug_lines=slug_lines)
    if issues:
        warning("Entries are not sorted in slug alphabetical order:")
        for issue in issues:
            warning("  - %s", issue)
        return True
    else:
        info("Entries are sorted in slug alphabetical order.")
        return False


def report_language_order(glossary, slug_lines):
    issues = check_language_order(glossary, slug_lines=slug_lines)
    if issues:
        warning("Entries with incorrect language code order:")
        for issue in issues:
            warning("  - %s", issue)
        return True
    else:
        info("Language codes in all entries are sorted alphabetically.")
        return False


def report_empty_defs(glossary, slug_lines):
    issues = check_def_not_empty(glossary, slug_lines=slug_lines)
    if issues:
        warning("Issues found with def fields:")
        for issue in issues:
            warning("  - %s", issue)
        return True
    else:
        info("All def fields are non-empty.")
        return False


def report_style(glossary, slug_lines, style_marker=">"):
    issues = check_def_style(glossary, style_marker, slug_lines=slug_lines)
    if issues:
        warning("YAML style issues found in def fields:")
        for issue in issues:
            warning("  - %s", issue)
        return True
    else:
        info("All def fields use the correct YAML folded style.")
        return False


def parse_args():
    parser = argparse.ArgumentParser(description="Glossary validation runner.")
    parser.add_argument(
        "--language-codes",
        "-l",
        type=Path,
        default=Path("language-codes.json"),
        help="Path to language-codes.json",
    )
    parser.add_argument(
        "--exit-on-error",
        action="store_true",
        help="Exit with non-zero code if any validation issue is found.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Running glossary check with args: {args}")

    glossary = load_glossary()
    if glossary is None:
        sys.exit(1)

    slug_lines = get_slug_line_map(glossary)
    if slug_lines is None:
        error("Failed to compute slug line map; aborting.")
        sys.exit(1)

    language_names = load_language_codes(args.language_codes)

    has_issues = False
    has_issues |= report_basic_format(glossary, slug_lines)
    has_issues |= report_ref_validity(glossary, slug_lines)
    has_issues |= report_cross_links(glossary, slug_lines, language_names)
    has_issues |= report_slug_order(glossary, slug_lines)
    has_issues |= report_language_order(glossary, slug_lines)
    has_issues |= report_empty_defs(glossary, slug_lines)
    has_issues |= report_style(glossary, slug_lines, style_marker=">")

    if args.exit_on_error and has_issues:
        error("Glossary validation found issues. Exiting with error.")
        sys.exit(1)

    info("Glossary check completed without critical errors.")


if __name__ == "__main__":
    main()
