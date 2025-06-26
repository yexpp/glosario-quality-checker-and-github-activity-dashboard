import re
from ruamel.yaml import YAML
import os

# File path
FILE_PATH = os.path.join(os.path.dirname(__file__), "glossary.yml")


# Regular expression definitions

# Slug can only contain lowercase letters, digits, and underscores
SLUG_PATTERN = re.compile(r'^[a-z0-9_]+$')
# ISO 639 language code consists of two lowercase letters
ISO_639_PATTERN = re.compile(r'^[a-z]{2}$') 

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

def validate_glossary(glossary):
    """
    Validate the format and structure of each glossary entry.
    Main checks:
    - Each entry must be a dictionary
    - Must contain a valid 'slug', unique and correctly formatted
    - If present, 'ref' field must be a list
    - Language codes must comply with ISO 639 standard
    - Each language entry must have language code and 'def' field with valid type and content
    - Check for duplicate slugs
    Returns a list of issues.
    """
    issues = []
    seen_slugs = set()
    for index, entry in enumerate(glossary):
        if not isinstance(entry, dict):
            issues.append(f"Entry #{index+1} is not a dictionary.")
            continue

        slug_value = entry.get("slug")
        if not slug_value:
            issues.append(f"Entry #{index+1} is missing the 'slug' key.")
            continue

        if not SLUG_PATTERN.fullmatch(slug_value):
            issues.append(f"slug '{slug_value}' has invalid format (must be lowercase, containing only alphanumeric and underscores).")

        if slug_value in seen_slugs:
            issues.append(f"slug '{slug_value}' is duplicated.")
        else:
            seen_slugs.add(slug_value)

        if "ref" in entry and not isinstance(entry["ref"], list):
            issues.append(f"'ref' in slug '{slug_value}' must be a list.")

        language_keys = []
        for key, value in entry.items():
            if key in {"slug", "ref"}:
                continue
            if not ISO_639_PATTERN.fullmatch(key):
                issues.append(f"Key '{key}' in slug '{slug_value}' is not a valid ISO 639 language code.")
                continue
            language_keys.append(key)

            if not isinstance(value, dict):
                issues.append(f"Value for language '{key}' in slug '{slug_value}' is not a dictionary.")
                continue

            if "term" not in value:
                issues.append(f"'term' is missing for language '{key}' in slug '{slug_value}'.")
            else:
                term_value = value["term"]
                if not isinstance(term_value, str):
                    issues.append(f"'term' for language '{key}' in slug '{slug_value}' is not a string.")
                elif not term_value.strip():
                    issues.append(f"'term' for language '{key}' in slug '{slug_value}' is empty or whitespace only.")

            if "def" not in value:
                issues.append(f"'def' is missing for language '{key}' in slug '{slug_value}'.")

        if not language_keys:
            issues.append(f"No language definition found in slug '{slug_value}'.")

    return issues

def check_ref_validity(glossary):
    """Check that all ref slugs referenced in glossary exist"""
    issues = []
    all_slugs = {entry['slug'] for entry in glossary if isinstance(entry, dict) and 'slug' in entry}

    for entry in glossary:
        slug_value = entry.get('slug')
        ref_list = entry.get('ref', [])
        if not isinstance(ref_list, list):
            continue
        for ref_slug in ref_list:
            if ref_slug not in all_slugs:
                issues.append(f"Entry '{slug_value}' has ref pointing to nonexistent slug '{ref_slug}'")
    return issues

def check_slug_order(glossary):
    """Check if entries are sorted alphabetically by slug"""
    issues = []
    slugs_list = [entry.get('slug', 'missing-slug') for entry in glossary if isinstance(entry, dict)]
    sorted_slugs = sorted(slugs_list)

    for index, (actual_slug, expected_slug) in enumerate(zip(slugs_list, sorted_slugs)):
        if actual_slug != expected_slug:
            expected_position = slugs_list.index(expected_slug) + 1 if expected_slug in slugs_list else "not found"
            issues.append(f"Entry {index+1} is currently '{actual_slug}', but should be '{expected_slug}' (current position {expected_position})")

    return issues

def check_language_order(glossary):
    """Check if language codes in each entry are sorted alphabetically"""
    issues = []
    for entry in glossary:
        if not isinstance(entry, dict):
            continue
        slug_value = entry.get('slug', 'missing-slug')
        language_keys = [key for key in entry.keys() if key not in {'slug', 'ref'}]
        if language_keys != sorted(language_keys):
            issues.append(f"Language codes in entry '{slug_value}' are not in alphabetical order: {language_keys}")
    return issues

def check_def_not_empty(glossary):
    """Check that all 'def' fields are not empty"""
    errors = []
    if not glossary:
        return errors
    for entry in glossary:
        slug = entry.get('slug', 'missing-slug')
        for language_code, content in entry.items():
            if language_code in ('slug', 'ref'):
                continue
            def_content = content.get('def', '') if content else ''
            if not def_content.strip():
                errors.append(f"'def' content for language '{language_code}' in entry '{slug}' is empty!")
    return errors

def check_def_style(glossary, style='>'):
    """Check that all 'def' fields use the specified YAML style (default folded style '>')"""
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
                        errors.append(
                            f"'def' for language '{language_code}' in entry '{slug}' is not folded style {style}, but '{sub_value.style}'"
                        )
    return errors

def check_cross_language_links(glossary):
    """
    Check consistency of cross-reference links among different languages,
    using the English ('en') version as the base, to detect missing links in other languages.
    """
    issues = []
    glossary_by_slug = {}
    for entry in glossary:
        if not isinstance(entry, dict):
            continue
        slug = entry["slug"]
        glossary_by_slug[slug] = {}
        for key, value in entry.items():
            if key not in {"slug", "ref"}:
                glossary_by_slug[slug][key] = value

    for slug, translations in glossary_by_slug.items():
        if 'en' not in translations:
            continue
        en_definition = translations['en'].get('def', '')
        en_links = set(re.findall(r'\[[^\]]+\]\(#([a-z0-9_]+)\)', en_definition))

        for language_code, content in translations.items():
            if language_code == 'en':
                continue
            definition_text = content.get('def', '')
            for link_slug in en_links:
                if not re.search(rf'\[.*?\]\(#{re.escape(link_slug)}\)', definition_text):
                    issues.append({
                        'slug': slug,
                        'lang': language_code,
                        'missing_link': link_slug,
                    })

    return issues
