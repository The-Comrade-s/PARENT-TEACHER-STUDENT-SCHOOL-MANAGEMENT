import streamlit as st

from components.ui import page_header, load_theme
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import search_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Search")

    query = st.text_input("Search students, teachers, parents, classes, or subjects")
    if not query:
        return

    results = search_service.global_search(query)
    any_results = False
    for category, items in results.items():
        if items:
            any_results = True
            st.subheader(category)
            for item in items:
                st.markdown(f'<div class="ptms-card">{item["label"]}</div>', unsafe_allow_html=True)

    if not any_results:
        st.info("No matching records found.")
