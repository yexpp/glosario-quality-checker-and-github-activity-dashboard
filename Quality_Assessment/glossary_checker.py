import re
import os
import base64
import traceback

from io import StringIO
from ruamel.yaml import YAML
from github import Github
from dotenv import load_dotenv

# GitHub repository information and file path configuration
GITHUB_OWNER = "carpentries"
GITHUB_REPO = "glosario"
GLOSSARY_FILE_PATH = "glossary.yml"

# Regex pattern to validate slugs: allows only lowercase letters, digits, and underscores
SLUG_PATTERN = re.compile(r'^[a-z0-9_]+$')

# Load environment variables from .env file if available
load_dotenv()


def get_glossary_yml_content(owner=GITHUB_OWNER,repo_name=GITHUB_REPO,file_path=GLOSSARY_FILE_PATH):
    """
    Fetch the content of a YAML file from a GitHub repository.
    
    Args:
        owner (str): GitHub repository owner username.
        repo_name (str): Repository name.
        file_path (str): Path to the file within the repository.
    
    Returns:
       str: File content decoded as UTF-8.

    Raises:
        RuntimeError: If token is missing or API request fails.
    """
    

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GitHub API token not found. "
            "Create a `.env` with GITHUB_TOKEN=your_token or set the environment variable."
        )

    try:
        g = Github(token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        file_content = repo.get_contents(file_path)
        content = base64.b64decode(file_content.content).decode("utf-8")
        return content
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {file_path} from {owner}/{repo_name}: {type(e).__name__}: {e}")

    
def load_yaml(yaml_str):
    """
    Parse a YAML string using ruamel.yaml and return the corresponding Python object.
    
    Args:
        yaml_str (str): YAML formatted string.
    
    Returns:
        object or None: Parsed Python object; None if parsing fails.
    """
    yaml_parser = YAML(typ='rt') 
    try:
        data = yaml_parser.load(StringIO(yaml_str)) 
        return data
    except Exception as e:
        print(f"Failed to parse YAML string: {type(e).__name__}: {e}")
        return None


def get_slug_line_map(glossary):
    """
    Return a dict mapping each slug to its line number (1-based).

    Args:
        glossary (list): List of glossary entry dicts.

    Returns:
        dict: Slug-to-line-number map. Line is None if unavailable.
    """
    slug_lines = {}
    if not glossary:
        return slug_lines
    for item in glossary:
        if isinstance(item, dict) and 'slug' in item:
            try:
                # Use ruamel.yaml's lc attribute to get line number of the 'slug' key
                # Lines are zero-based, so add 1 for human-readable format
                line = item.lc.key('slug')[0] + 1
            except AttributeError:
                # Warn if line number info is missing
                print(f"Warning: missing line info for item with slug '{item.get('slug')}'")
                line = None
            slug = item['slug']
            slug_lines[slug] = line
    return slug_lines


def format_line_info(slug, slug_lines):
    """
    Format the line number information for a given slug as a string for display.
    
    Args:
        slug (str): The slug string.
        slug_lines (dict): Mapping from slugs to their line numbers.
    
    Returns:
        str: Formatted line info string ; empty string if unavailable.
    """
    if not slug_lines or not slug:
        return ""
    line = slug_lines.get(slug)
    if line is None:
        return ""
    return f" (line {line})"


def iter_valid_entries(glossary):
    """
    Yield glossary entries that are dictionaries containing a 'slug' key.
    
    Args:
        glossary (list): List of glossary entries (dicts).
    
    Yields:
        dict: Valid entry with a 'slug' key.
    """
    for entry in glossary:
        if isinstance(entry, dict) and 'slug' in entry:
            yield entry


def get_entry_slug_and_line(entry, slug_lines):
    """
    Retrieve the slug and formatted line number information for a given glossary entry.
    
    Args:
        entry (dict): A glossary entry dictionary expected to have a 'slug' key.
        slug_lines (dict): Mapping of slug strings to their line numbers.
    
    Returns:
        tuple: (slug (str), line_info (str)) where line_info is formatted like " (line X)" or empty string.
    """   
    slug = entry.get('slug', 'missing-slug')
    line_info = format_line_info(slug, slug_lines)
    return slug, line_info


def get_language_entries(entry):
    """
    Extract all key-value pairs from a glossary entry except the keys 'slug' and 'ref'.
    
    Args:
        entry (dict): A glossary entry dictionary.
    
    Returns:
        dict: A new dictionary excluding the 'slug' and 'ref' keys.
    """
    return {k: v for k, v in entry.items() if k not in {"slug", "ref"}}


def validate_glossary(glossary, slug_lines=None):
    """
    Validate a list of glossary entries for structural and content correctness.

    Args:
        glossary (list of dict): List of glossary entries. Each entry must be a dictionary
            containing at least a 'slug' key and language-specific sub-entries.
        slug_lines (dict, optional): Mapping from slug to line information for improved error messages.

    Returns:
        list of str: List of error messages found during validation.
            Empty list means no issues were found.
    """
    issues = []
    seen_slugs = set()

    valid_entries = []
    for index, entry in enumerate(glossary):
        line_info = f" (entry #{index+1})"  
        if not isinstance(entry, dict):
            issues.append(f"Entry #{index+1} is not a dictionary.")
            continue
        if 'slug' not in entry:
            issues.append(f"Entry #{index+1} is missing the 'slug' key.")
            continue
        valid_entries.append(entry)


    for entry in valid_entries:
        slug, line_info = get_entry_slug_and_line(entry, slug_lines)

        if not SLUG_PATTERN.fullmatch(slug):
            issues.append(f"Slug '{slug}'{line_info} has invalid format (must be lowercase, alphanumeric and underscores).")

        if slug in seen_slugs:
            issues.append(f"Slug '{slug}'{line_info} is duplicated.")
        else:
            seen_slugs.add(slug)

        if "ref" in entry and not isinstance(entry["ref"], list):
            issues.append(f"'ref' in slug '{slug}'{line_info} must be a list.")

        lang_entries = get_language_entries(entry)
        if not lang_entries:
            issues.append(f"No language entries found in slug '{slug}'{line_info}.")

        for lang, value in lang_entries.items():
            if not isinstance(value, dict):
                issues.append(f"Value for language '{lang}' in slug '{slug}'{line_info} is not a dictionary.")
                continue

            term_value = value.get("term")
            if term_value is None:
                issues.append(f"'term' is missing for language '{lang}' in slug '{slug}'{line_info}.")
            elif not isinstance(term_value, str):
                issues.append(f"'term' for language '{lang}' in slug '{slug}'{line_info} is not a string.")
            elif not term_value.strip():
                issues.append(f"'term' for language '{lang}' in slug '{slug}'{line_info} is empty or whitespace only.")

    return issues


def check_def_not_empty(glossary, slug_lines=None):
    """
    Check that all 'def' fields in glossary entries are non-empty strings.

    Args:
        glossary (list of dict): List of glossary entries. Each entry is a dictionary that should
            contain language-specific sub-entries, each potentially having a 'def' field.
        slug_lines (dict, optional): Mapping from slug to line information for improved error messages.

    Returns:
        list of str: List of error messages for entries where 'def' is missing, empty, or invalid.
            Returns an empty list if no issues are found.
    """
    errors = []
    if not glossary:
        return errors

    for entry in iter_valid_entries(glossary):
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
    """
    Check that all 'def' fields in glossary entries use the specified YAML folded style.

    Args:
        glossary (object): YAML parsed glossary object where entries and their fields
            are accessible via `.value` attributes.
        style (str): The expected YAML style indicator for 'def' fields (default is '>').
        slug_lines (dict, optional): Mapping from slug to line information for improved error messages.

    Returns:
        list of str: List of error messages for 'def' fields not using the specified folded style.
            Returns an empty list if no issues are found.
    """
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
                            f"'def' for language '{language_code}' in entry '{slug}'{line_info} is not folded style {style}, but '{sub_value.style}'!"
                        )
    return errors



def check_ref_validity(glossary, slug_lines=None):
    """
    Check that all referenced slugs exist in the glossary.

    Args:
        glossary: Glossary entries containing references.
        slug_lines: Optional dict mapping slugs to line info.

    Returns:
        List of reference issues with nonexistent slugs.
    """
    issues = []
    all_slugs = {entry['slug'] for entry in iter_valid_entries(glossary)}

    for entry in iter_valid_entries(glossary):
        slug, line_info = get_entry_slug_and_line(entry, slug_lines)
        ref_list = entry.get('ref', [])
        if not isinstance(ref_list, list):
            continue
        for ref_slug in ref_list:
            if ref_slug not in all_slugs:
                issues.append(f"Entry '{slug}'{line_info} has ref pointing to nonexistent slug '{ref_slug}'.")
    return issues


def check_slug_order(glossary, slug_lines=None):
    """
    Check whether slugs, in file line order, are sorted alphabetically.

    Args:
        glossary: Glossary entries to check.
        slug_lines: Optional dict mapping slugs to line numbers.

    Returns:
        List of slugs with ordering issues.
    """
    issues = []
    slug_lines = slug_lines or {}

    valid_entries = list(iter_valid_entries(glossary))

    valid_entries = sorted(valid_entries, key=lambda e: slug_lines.get(e['slug'], 999999))
    slugs_file_order = [entry['slug'] for entry in valid_entries]


    slugs_alpha_order = sorted(slugs_file_order)
    slug_to_alpha_index = {slug: i for i, slug in enumerate(slugs_alpha_order)}

    reported_slugs = set()

    for i, slug in enumerate(slugs_file_order):
        alpha_pos = slug_to_alpha_index[slug]
        for later_slug in slugs_file_order[i+1:]:
            if slug_to_alpha_index[later_slug] < alpha_pos:
                if later_slug not in reported_slugs:
                    line_num = slug_lines.get(later_slug, 'unknown line number')
                    issues.append(f"Slug'{later_slug}' (line {line_num}) is out of order.")
                    reported_slugs.add(later_slug)
               
    return issues


def check_cross_language_links(glossary, slug_lines=None):
    """
    Check that links in English definitions appear in other languages too.
    
    Args:
        glossary: Glossary entries with multilingual definitions.
        slug_lines: Optional mapping of slugs to line info.
        
    Returns:
        List of issues where links are missing in other languages.
    """
    
    issues = []
    glossary_by_slug = {}

    for entry in iter_valid_entries(glossary):
        slug, _ = get_entry_slug_and_line(entry, slug_lines)
        glossary_by_slug[slug] = get_language_entries(entry)

    for slug, translations in glossary_by_slug.items():
        en_def = translations.get('en', {}).get('def', '')
        en_links = set(re.findall(r'\[[^\]]+]\(#([a-z0-9_]+)\)', en_def))

        for lang, content in translations.items():
            if lang == 'en':
                continue
            def_text = content.get('def', '')
            for link_slug in en_links:
                if not re.search(rf'\[.*?]\(#{re.escape(link_slug)}\)', def_text):
                    line_info = format_line_info(slug, slug_lines)
                    issues.append({
                        'slug': slug,
                        'lang': lang,
                        'missing_link': link_slug,
                        'line': line_info
                    })

    return issues


def check_language_order(glossary, slug_lines=None):
    """
    Ensure language codes are ordered alphabetically or with 'en' first.

    Args:
        glossary: Glossary entries with multilingual content.
        slug_lines: Optional dict mapping slugs to line info.

    Returns:
        List of entries with incorrect language order.
    """
    issues = []
    
    for entry in iter_valid_entries(glossary):
        slug, line_info = get_entry_slug_and_line(entry, slug_lines or {})
        language_keys = list(get_language_entries(entry).keys())

        sorted_all = sorted(language_keys)
        sorted_en_first = (['en'] if 'en' in language_keys else []) + sorted(k for k in language_keys if k != 'en')

        if language_keys != sorted_all and language_keys != sorted_en_first:
            issues.append(f"Entry '{slug}'{line_info}: {language_keys}")

    return issues

