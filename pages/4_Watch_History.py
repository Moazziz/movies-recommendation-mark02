"""
pages/4_Watch_History.py
Shows the last 20 movies the user searched / clicked "Recommend" on.
"""

import streamlit as st

st.set_page_config(page_title="Watch History | MOAZZIZ", page_icon="🕐", layout="wide")

if "user" not in st.session_state:
    st.warning("🔒 Please log in first.")
    if st.button("← Go to Login", key="login_redirect"):
        st.switch_page("app.py")
    st.stop()

from database   import get_history
from ui_helpers import inject_css, render_topbar, section_header
from nav_helper import render_sidebar
from recommender import fetch_poster

inject_css()
render_topbar()
render_sidebar(current="hist")

user_id = st.session_state["user"]["id"]
history = get_history(user_id)

section_header("🕐 Your Watch History")
st.markdown("*Tracks every movie you searched for a recommendation on.*")

if not history:
    st.info("No history yet — start searching for movies!")
else:
    for record in history:
        col_img, col_info = st.columns([1, 6])
        with col_img:
            st.image(fetch_poster(record["movie_title"]), width=60)
        with col_info:
            ts = (
                record["watched_at"].strftime("%d %b %Y, %H:%M")
                if hasattr(record["watched_at"], "strftime")
                else str(record["watched_at"])
            )
            st.markdown(
                f"**{record['movie_title']}** &nbsp;&nbsp;"
                f"<span style='color:#888;font-size:12px'>🕐 {ts}</span>",
                unsafe_allow_html=True,
            )
            if st.button(
                "🔍 Recommend similar",
                key=f"hist_{record['movie_title']}_{ts}",
            ):
                st.session_state["selected_movie"] = record["movie_title"]
                st.switch_page("pages/1_Recommendations.py")
        st.markdown(
            "<hr style='border:0;border-top:1px solid #2a2a3e;margin:6px 0'>",
            unsafe_allow_html=True,
        )