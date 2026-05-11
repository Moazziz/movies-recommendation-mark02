"""
ui_helpers.py  –  Shared Streamlit UI components
"""

import streamlit as st
from recommender import fetch_poster
from database import add_favourite, remove_favourite, get_favourites, add_to_history


# ──────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ── base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f0f0f;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background-color: #1a1a2e;
}

/* ── hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── top nav bar ── */
.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
    padding: 14px 28px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(187,134,252,0.15);
}
.logo { font-size: 30px; font-weight: 900; color: #bb86fc; letter-spacing: 2px; }
.user-chip {
    background: #bb86fc22;
    border: 1px solid #bb86fc66;
    color: #bb86fc;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
}

/* ── section headers ── */
.section-header {
    font-size: 22px;
    font-weight: 700;
    color: #bb86fc;
    margin: 28px 0 12px;
    border-left: 4px solid #bb86fc;
    padding-left: 10px;
}

/* ── movie card ── */
.movie-card {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 0 0 10px;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}
.movie-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(187,134,252,0.25);
}
.movie-title {
    font-size: 13px;
    font-weight: 600;
    color: #e0e0e0;
    padding: 8px 8px 2px;
    line-height: 1.3;
    min-height: 40px;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin: 4px 8px 0;
}
.badge-purple  { background: #bb86fc33; color: #bb86fc; border: 1px solid #bb86fc66; }
.badge-red     { background: #E5091422; color: #ff5555; border: 1px solid #E5091488; }
.badge-green   { background: #14A44D22; color: #2ecc71; border: 1px solid #14A44D88; }
.badge-gold    { background: #FFD70022; color: #FFD700; border: 1px solid #FFD70088; }
.badge-blue    { background: #1E90FF22; color: #1E90FF; border: 1px solid #1E90FF88; }

/* ── search bar ── */
.stSelectbox > div > div { background: #1e1e2e !important; color: #e0e0e0 !important; border-radius: 8px !important; }

/* ── buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #bb86fc, #8b5cf6);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    padding: 8px 20px;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }

/* ── auth form ── */
.auth-container {
    max-width: 420px;
    margin: 60px auto;
    background: #1a1a2e;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 8px 40px rgba(187,134,252,0.15);
    border: 1px solid #bb86fc33;
}
.auth-title {
    font-size: 26px;
    font-weight: 900;
    color: #bb86fc;
    text-align: center;
    margin-bottom: 28px;
}
.stTextInput input {
    background: #0f0f0f !important;
    color: #e0e0e0 !important;
    border: 1px solid #bb86fc44 !important;
    border-radius: 8px !important;
}

/* ── score bar ── */
.score-row { display: flex; gap: 6px; flex-wrap: wrap; padding: 0 8px; margin-top: 4px; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# TOP NAV BAR
# ──────────────────────────────────────────────
def render_topbar():
    user = st.session_state.get("user")
    chip = f'<span class="user-chip">👤 {user["username"]}</span>' if user else ""
    st.markdown(
        f"""
        <div class="topbar">
            <div class="logo">🎬 MOAZZIZ</div>
            {chip}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# MOVIE CARD
# ──────────────────────────────────────────────
def movie_card(
    col,
    title: str,
    vote_average: float = 0.0,
    badge_label: str = "",
    badge_class: str = "badge-purple",
    similarity: float | None = None,
    final_score: float | None = None,
    show_fav_btn: bool = False,
):
    """Render a single movie card inside a Streamlit column."""
    with col:
        poster = fetch_poster(title)
        st.image(poster, use_container_width=True)

        # title + scores
        scores_html = ""
        if vote_average:
            scores_html += f'<span class="badge badge-green">⭐ {round(vote_average,1)}</span>'
        if similarity is not None:
            scores_html += f'<span class="badge badge-blue">🎯 {round(similarity,2)}</span>'
        if final_score is not None:
            scores_html += f'<span class="badge badge-purple">🔥 {round(final_score,2)}</span>'

        badge_html = f'<div class="badge {badge_class}">{badge_label}</div>' if badge_label else ""

        st.markdown(
            f"""
            <div class="movie-title">{title}</div>
            {badge_html}
            <div class="score-row">{scores_html}</div>
            """,
            unsafe_allow_html=True,
        )

        # favourite button (only when logged in)
        if show_fav_btn and st.session_state.get("user"):
            user_id = st.session_state["user"]["id"]
            favs    = st.session_state.get("favourites", [])
            is_fav  = title in favs
            label   = "❤️ Saved" if is_fav else "🤍 Save"

            if st.button(label, key=f"fav_{title}_{badge_label}"):
                if is_fav:
                    remove_favourite(user_id, title)
                    st.session_state["favourites"].remove(title)
                    st.toast(f"Removed '{title}' from favourites.")
                else:
                    add_favourite(user_id, title)
                    if "favourites" not in st.session_state:
                        st.session_state["favourites"] = []
                    st.session_state["favourites"].append(title)
                    st.toast(f"❤️ Added '{title}' to favourites!")
                st.rerun()


# ──────────────────────────────────────────────
# SECTION HEADER
# ──────────────────────────────────────────────
def section_header(label: str):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# MOVIE ROW (5 cards)
# ──────────────────────────────────────────────
def movie_row(
    df,
    badge_label: str = "",
    badge_class: str = "badge-purple",
    show_scores: bool = False,
    show_fav: bool = True,
    n: int = 5,
):
    """Render up to n movies in a horizontal row of columns."""
    df = df.head(n)
    cols = st.columns(n)
    for idx, (_, row) in enumerate(df.iterrows()):
        movie_card(
            col         = cols[idx % n],
            title       = row["title"],
            vote_average= row.get("vote_average", 0),
            badge_label = badge_label,
            badge_class = badge_class,
            similarity  = row.get("similarity") if show_scores else None,
            final_score = row.get("final_score") if show_scores else None,
            show_fav_btn= show_fav,
        )
