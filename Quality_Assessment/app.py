import streamlit as st
import pandas as pd
from pathlib import Path
from glossary_check_runner import run_glossary_check

# Page settings
st.set_page_config(page_title="Glossary Validation Tool", page_icon="📚", layout="wide")
st.title("📚 Glossary Validation Tool")

# Store results in session_state
if "glossary_result" not in st.session_state:
    st.session_state.glossary_result = None

# Sidebar parameters
st.sidebar.header("⚙ Settings")
language_path = st.sidebar.text_input("Path to language-codes.json", "language-codes.json")

# Run validation on button click

if st.sidebar.button("🔍 Run Validation"):
    file_path = Path(language_path)
    if not file_path.exists():
        st.error(f" File not found: {language_path}")
        st.session_state.glossary_result = None
    else:
        with st.spinner("Validating Glossary..."):
            st.session_state.glossary_result = run_glossary_check(language_path)

result = st.session_state.get("glossary_result")

# Main content display
if result is not None:

    # Validation results table

    if "results" in result:
        st.subheader("📝 Validation Results")
        df_results = [{"Check": name, "Status": status} for name, status in result["results"]]
        st.table(df_results)

    # Detailed Issues and check descriptions
    if "logs" in result:
        st.subheader("📜 Detailed Issues")

        check_options = list(result["logs"].keys())
        selected_check = st.selectbox("Select a check to view its details", check_options)

        # check standard
        check_descriptions = {
            "Basic Format Validation": "Check whether the Glossary file meets the basic structure and field format requirements:\n1. Verify that each slug exists and is valid (only lowercase letters, numbers, and underscores are allowed).\n2. If a ref field exists, it must be a list.\n3. Each language entry must be a dictionary, and each language must contain a non-empty 'term' field.",
            "Reference validity check": " Check that all referenced slugs exist in the glossary.",
            "Reference Consistency Check": " Check that links in English definitions also appear in other languages.",
            "Slug Order Check": " Verify that all glossary slugs are listed in alphabetical order.",
            "Language Code Order Check": " Ensure language codes are either fully in alphabetical order, or with 'en' first and the remaining codes in alphabetical order.",
            "Definition Fields Format check": "Check that all 'def' fields in glossary entries use the specified YAML folded style.。",
            "Definition Fields Non-empty check": "Check that all 'def' fields in glossary entries are non-empty strings.",

        }

        if selected_check in check_descriptions:
            st.info(f"📘 **check standard：** {check_descriptions[selected_check]}")

        for level, text in result["logs"][selected_check]:
            if level == "INFO":
                st.info(text)
            elif level == "WARNING":
                st.warning(text)
            else:
                st.error(text)

    # Success or failure message
    if result.get("success", False):
        st.success("🎉 All validation checks passed!")
    else:
        st.warning("⚠️ Some checks found issues. Please select a specific check to view details.")

else:
    st.info("Please click the button on the left to start validation.")

# Footer
st.write("---")
st.caption("© Developed by yexpp · Streamlit UI version")
