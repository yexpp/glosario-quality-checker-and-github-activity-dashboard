import re
from ruamel.yaml import YAML
import os

# File path
FILE_PATH = os.path.join(os.path.dirname(__file__), "glossary.yml")

# Regular expression definitions
# Slug can only contain lowercase letters, digits, and underscores
SLUG_PATTERN = re.compile(r'^[a-z0-9_]+$')

def load_yaml(file_path):
    """Load yaml file and return glossary content"""
    yaml_parser = YAML()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            glossary = yaml_parser.load(file)
        return glossary
    except Exception as exception:
        print(f"Failed to load YAML file: {exception}")
        return None

def get_slug_line_map(glossary):
    """Extract a mapping of slug to its line number"""
    slug_lines = {}
    for item in glossary:
        if isinstance(item, dict) and 'slug' in item:
            line = item.lc.key('slug')[0] + 1
            slug = item['slug']
            slug_lines[slug] = line
    return slug_lines

def format_line_info(slug, slug_lines):
    """Get the line number associated with the slug"""
    if not slug_lines or not slug:
        return ""
    line = slug_lines.get(slug)
    if line is None:
        return ""
    return f" (line {line})"

def validate_glossary(glossary, slug_lines=None):
    """
    Validate the format and structure of each glossary entry.
    Main checks:
    - Each entry must be a dictionary
    - Must contain a valid 'slug', unique and correctly formatted
    - If present, 'ref' field must be a list
    - Each language entry must have language code
    - Check for duplicate slugs
    Returns a list of issues.
    """
    issues = []
    seen_slugs = set()

    for index, entry in enumerate(glossary):
        if not isinstance(entry, dict):
            issues.append(f"Entry #{index+1} is not a dictionary.")
            continue

        slug = entry.get("slug")
        line_info = format_line_info(slug, slug_lines)

        if not slug:
            issues.append(f"Entry #{index+1} is missing the 'slug' key.")
            continue

        if not SLUG_PATTERN.fullmatch(slug):
            issues.append(f"Slug '{slug}' {line_info} has invalid format (must be lowercase, alphanumeric and underscores).")

        if slug in seen_slugs:
            issues.append(f"Slug '{slug}' {line_info} is duplicated.")
        else:
            seen_slugs.add(slug)

        if "ref" in entry and not isinstance(entry["ref"], list):
            issues.append(f"'ref' in slug '{slug}' {line_info} must be a list.")

        language_keys = []
        for key, value in entry.items():
            if key in {"slug", "ref"}:
                continue

            language_keys.append(key)

            if not isinstance(value, dict):
                issues.append(f"Value for language '{key}' in slug '{slug}' {line_info} is not a dictionary.")
                continue

            if "term" not in value:
                issues.append(f"'term' is missing for language '{key}' in slug '{slug}' {line_info}.")
            else:
                term_value = value["term"]
                if not isinstance(term_value, str):
                    issues.append(f"'term' for language '{key}' in slug '{slug}' {line_info} is not a string.")
                elif not term_value.strip():
                    issues.append(f"'term' for language '{key}' in slug '{slug}' {line_info} is empty or whitespace only.")

        if not language_keys:
            issues.append(f"No language codes found in slug '{slug}' {line_info}.")

    return issues

def check_cross_language_links(glossary, slug_lines=None):
    """
    Check consistency of cross-reference links among different languages,
    using the English ('en') version as the base, to detect missing links in other languages.
    """
    issues = []
    glossary_by_slug = {}

    for entry in glossary:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug")
        if not slug:
            continue
        glossary_by_slug[slug] = {}
        for key, value in entry.items():
            if key not in {"slug", "ref"}:
                glossary_by_slug[slug][key] = value

    for slug, translations in glossary_by_slug.items():
        if 'en' not in translations:
            continue

        en_definition = translations['en'].get('def', '')
        en_links = set(re.findall(r'\[[^\]]+]\(#([a-z0-9_]+)\)', en_definition))

        for language_code, content in translations.items():
            if language_code == 'en':
                continue
            definition_text = content.get('def', '')
            for link_slug in en_links:
                if not re.search(rf'\[.*?]\(#{re.escape(link_slug)}\)', definition_text):
                    line_info = format_line_info(slug, slug_lines)
                    issues.append({
                        'slug': slug,
                        'lang': language_code,
                        'missing_link': link_slug,
                        'line': line_info
                    })

    return issues

def check_ref_validity(glossary, slug_lines=None):
    """Check that all ref slugs referenced in glossary exist"""
    issues = []
    all_slugs = {entry['slug'] for entry in glossary if isinstance(entry, dict) and 'slug' in entry}

    for entry in glossary:
        slug = entry.get('slug')
        ref_list = entry.get('ref', [])
        if not isinstance(ref_list, list):
            continue
        for ref_slug in ref_list:
            if ref_slug not in all_slugs:
                line_info = format_line_info(slug, slug_lines)
                issues.append(
                    f"Entry '{slug}'{line_info} has ref pointing to nonexistent slug '{ref_slug}'"
                )
    return issues

def check_slug_order(glossary, slug_lines=None):
    """Check if entries are sorted alphabetically by slug, show first misplaced item with line number"""
    issues = []
    slugs_list = [entry['slug'] for entry in glossary if isinstance(entry, dict) and 'slug' in entry]
    sorted_slugs = sorted(slugs_list)

    for index, (actual_slug, expected_slug) in enumerate(zip(slugs_list, sorted_slugs)):
        if actual_slug != expected_slug:
            actual_line = slug_lines.get(actual_slug, '?') if slug_lines else '?'
            expected_line = slug_lines.get(expected_slug, '?') if slug_lines else '?'
            issues.append(
                f"Slug '{expected_slug}'(line {expected_line}) should be before '{actual_slug}' (currently at line {actual_line})"
            )
            break
    return issues

def check_language_order(glossary, slug_lines=None):
    """
    Check if language codes in each glossary entry follow an accepted order:
    Either fully alphabetical,Or with 'en' first, followed by the rest in alphabetical order 
    """
    issues = []
    for entry in glossary:
        if not isinstance(entry, dict):
            continue
        slug = entry.get('slug', 'missing-slug')
        language_keys = [key for key in entry.keys() if key not in {'slug', 'ref'}]

        sorted_all = sorted(language_keys)

        sorted_en_first = (['en'] if 'en' in language_keys else []) + sorted(k for k in language_keys if k != 'en')

        if language_keys != sorted_all and language_keys != sorted_en_first:
            line_info = format_line_info(slug, slug_lines)
            issues.append(f"Entry '{slug}'{line_info}: {language_keys}")

    return issues

def check_def_not_empty(glossary, slug_lines=None):
    """Check that all 'def' fields are not empty"""
    errors = []
    if not glossary:
        return errors

    for entry in glossary:
        slug = entry.get('slug', 'missing-slug')
        for language_code, content in entry.items():
            if language_code in ('slug', 'ref'):
                continue
            def_content = content.get('def', '') if isinstance(content, dict) else ''
            if not isinstance(def_content, str) or not def_content.strip():
                line_info = format_line_info(slug, slug_lines)
                errors.append(
                    f"'def' content for language '{language_code}' in entry '{slug}'{line_info} is empty or invalid!"
                )
    return errors

def check_def_style(glossary, style='>', slug_lines=None):
    """Check that all 'def' fields use the specified folded style and report mismatches"""
    errors = []
    if not glossary or not hasattr(glossary, 'value'):
        return errors
    for entry in glossary.value:
        slug = None
        for key, value in entry.value:
            if key.value == 'slug':
                slug = value.value
        for key, value in entry.value:
            language_code = key.value
            if language_code in ('slug', 'ref'):
                continue
            for sub_key, sub_value in value.value:
                if sub_key.value == 'def':
                    if sub_value.style != style:
                        line_info = format_line_info(slug, slug_lines)
                        errors.append(
                            f"'def' for language '{language_code}' in entry '{slug}'{line_info} is not folded style {style}, but '{sub_value.style}'"
                        )
    return errors
