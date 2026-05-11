"""
recommender.py  –  Content-based + popularity hybrid recommendation engine
Loaded once and cached by Streamlit so it is fast on every request.
"""

import ast
import numpy as np
import pandas as pd
import requests
import streamlit as st
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


# ──────────────────────────────────────────────
# TMDB API KEY
# ──────────────────────────────────────────────
API_KEY = "719ef9ab8869eefb4dd604c6e1ab6f32"


# ──────────────────────────────────────────────
# DATA LOADING  (cached – runs only once)
# ──────────────────────────────────────────────
@st.cache_data(show_spinner="📂 Loading movie database…")
def load_data(movies_path: str, credits_path: str) -> pd.DataFrame:
    """
    Load and preprocess the TMDB movies + credits CSVs.

    Parameters
    ----------
    movies_path  : path to tmdb_5000_movies.csv
    credits_path : path to tmdb_5000_credits.csv
    """
    movies  = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)

    movies = movies.merge(credits, on="title")
    movies = movies[[
        "movie_id", "title", "overview",
        "genres", "keywords", "cast", "crew",
        "vote_average", "popularity", "vote_count",
    ]]

    # ── helper converters ───────────────────────
    def _names(text):
        return [i["name"] for i in ast.literal_eval(text)]

    def _top3_cast(text):
        return [v["name"] for idx, v in enumerate(ast.literal_eval(text)) if idx < 3]

    def _director(text):
        return [i["name"] for i in ast.literal_eval(text) if i["job"] == "Director"]

    def _clean(lst):
        return [s.replace(" ", "") for s in lst]

    movies["genres"]   = movies["genres"].apply(_names).apply(_clean)
    movies["keywords"] = movies["keywords"].apply(_names).apply(_clean)
    movies["cast"]     = movies["cast"].apply(_top3_cast).apply(_clean)
    movies["crew"]     = movies["crew"].apply(_director).apply(_clean)
    movies["overview"] = movies["overview"].fillna("")

    # ── tag bag-of-words ────────────────────────
    movies["tags"] = (
        movies["overview"] + " "
        + movies["genres"].apply(" ".join) + " "
        + movies["keywords"].apply(" ".join) + " "
        + movies["cast"].apply(" ".join) + " "
        + movies["crew"].apply(" ".join)
    )

    # ── pre-compute popularity score ────────────
    movies = _add_popularity_score(movies)

    return movies.reset_index(drop=True)


def _add_popularity_score(df: pd.DataFrame) -> pd.DataFrame:
    """Normalised popularity + log-vote-count blend (weights: 70 / 30)."""
    pop_min, pop_max = df["popularity"].min(), df["popularity"].max()
    df["popularity_norm"] = (df["popularity"] - pop_min) / (pop_max - pop_min + 1e-9)

    vc_log = np.log1p(df["vote_count"])
    vc_min, vc_max = vc_log.min(), vc_log.max()
    df["vote_count_log_norm"] = (vc_log - vc_min) / (vc_max - vc_min + 1e-9)

    df["popularity_score"] = (
        0.7 * df["popularity_norm"]
        + 0.3 * df["vote_count_log_norm"]
    )
    return df


# ──────────────────────────────────────────────
# SIMILARITY MATRIX  (cached)
# ──────────────────────────────────────────────
@st.cache_data(show_spinner="🔢 Building similarity matrix…")
def compute_similarity(tags: pd.Series) -> np.ndarray:
    cv      = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(tags).toarray()
    return cosine_similarity(vectors)


# ──────────────────────────────────────────────
# CORE RECOMMENDATION PIPELINE
# ──────────────────────────────────────────────
def recommend_movies(
    movie_name: str,
    movies_df:  pd.DataFrame,
    cosine_sim: np.ndarray,
    top_n:      int = 10,
    min_rating: float = 6.5,
) -> pd.DataFrame | None:
    """
    Full 4-layer recommendation pipeline.

    Layer 1 – content similarity (cosine on tags)
    Layer 2 – IMDb quality filter  (vote_average ≥ min_rating)
    Layer 3 – popularity score merge
    Layer 4 – hybrid final ranking  (similarity 50 % | IMDb 30 % | popularity 20 %)

    Returns a DataFrame with columns:
        title, vote_average, similarity,
        popularity_score, imdb_norm, final_score
    or None if the movie isn't found / nothing passes the filter.
    """
    if movie_name not in movies_df["title"].values:
        return None

    idx = movies_df[movies_df["title"] == movie_name].index[0]

    # Layer 1 – similarity candidates (top 20 before filtering)
    sim_scores = sorted(
        enumerate(cosine_sim[idx]),
        key=lambda x: x[1],
        reverse=True,
    )[1:21]

    indices    = [s[0] for s in sim_scores]
    sim_values = [s[1] for s in sim_scores]

    rec = movies_df.iloc[indices][["title", "vote_average", "popularity_score"]].copy()
    rec["similarity"] = sim_values

    # Layer 2 – IMDb filter
    rec = rec[rec["vote_average"] >= min_rating]
    if rec.empty:
        return None

    # Layer 4 – hybrid score
    va_min, va_max = rec["vote_average"].min(), rec["vote_average"].max()
    rec["imdb_norm"] = (rec["vote_average"] - va_min) / (va_max - va_min + 1e-9)

    rec["final_score"] = (
        0.50 * rec["similarity"]
        + 0.30 * rec["imdb_norm"]
        + 0.20 * rec["popularity_score"]
    )

    rec = rec.sort_values("final_score", ascending=False).head(top_n)
    return rec.reset_index(drop=True)


# ──────────────────────────────────────────────
# GENRE-BASED BROWSE
# ──────────────────────────────────────────────
def movies_by_genre(genre: str, movies_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return top-N movies for a given genre sorted by popularity_score."""
    mask = movies_df["genres"].apply(
        lambda g: genre.replace(" ", "").lower() in [x.lower() for x in g]
    )
    return (
        movies_df[mask]
        .sort_values("popularity_score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def all_genres(movies_df: pd.DataFrame) -> list[str]:
    """Return a sorted, deduplicated list of all genres."""
    genres = set()
    for g_list in movies_df["genres"]:
        for g in g_list:
            genres.add(g)
    return sorted(genres)


# ──────────────────────────────────────────────
# POSTER FETCHER
# ──────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=86_400)
def fetch_poster(movie_title: str) -> str:
    """Fetch TMDB poster URL; returns a placeholder on failure."""
    try:
        url  = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_title}"
        data = requests.get(url, timeout=2).json()
        if data.get("results"):
            path = data["results"][0].get("poster_path")
            print("api data:  ",data)
            if path:
                return f"https://image.tmdb.org/t/p/w300{path}"
    except Exception:
        pass
    return "https://via.placeholder.com/300x450?text=No+Poster"


## my upgrade

# ──────────────────────────────────────────────
# AI DESCRIPTION RECOMMENDER
# ──────────────────────────────────────────────

@st.cache_data(show_spinner="🤖 Building AI recommender...")
def build_tfidf_matrix(tags):

    tfidf = TfidfVectorizer(stop_words='english')

    matrix = tfidf.fit_transform(tags)

    return tfidf, matrix


def recommend_by_description(
    user_text,
    movies_df,
    top_n=10
):

    tfidf, tfidf_matrix = build_tfidf_matrix(
        movies_df['tags']
    )

    user_vector = tfidf.transform([user_text])

    similarity = cosine_similarity(
        user_vector,
        tfidf_matrix
    )

    similarity = similarity.flatten()

    top_indices = similarity.argsort()[-top_n:][::-1]

    return movies_df.iloc[top_indices]