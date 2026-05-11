"""
nav_helper.py  –  shared sidebar navigation for all MOAZZIZ pages.
Import with:  from nav_helper import render_sidebar
"""

import streamlit as st


def render_sidebar(current: str = "home"):
    """
    Render the sidebar navigation.

    Parameters
    ----------
    current : str
        Key of the currently active page so its button is disabled.
        One of: 'home' | 'reco' | 'genre' | 'fav' | 'hist'
    """
    _pages = [
        ("home",  "app.py",                      "🏠 Home"),
        ("reco",  "pages/1_Recommendations.py",  "🔍 Recommendations"),
        ("genre", "pages/2_Browse_by_Genre.py",  "🗂️  Browse by Genre"),
        ("fav",   "pages/3_My_Favourites.py",    "❤️  My Favourites"),
        ("hist",  "pages/4_Watch_History.py",    "🕐 Watch History"),
    ]

    with st.sidebar:
        # Force sidebar to always stay open on every page
        st.markdown(
            """
            <style>
                button[kind="header"]              { display: none !important; }
                [data-testid="collapsedControl"]   { display: none !important; }
                section[data-testid="stSidebar"] {
                    min-width: 240px !important;
                    max-width: 240px !important;
                    transform: none !important;
                    visibility: visible !important;
                }
                section[data-testid="stSidebar"][aria-expanded="false"] {
                    transform: none !important;
                    margin-left: 0 !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("## 🎬 Navigation")
        for key, path, label in _pages:
            if st.button(
                label,
                use_container_width=True,
                key=f"nav_{key}",
                disabled=(key == current),
            ):
                st.switch_page(path)
        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True, key="nav_logout"):
            for k in ["user", "favourites", "selected_movie"]:
                st.session_state.pop(k, None)
            st.rerun()