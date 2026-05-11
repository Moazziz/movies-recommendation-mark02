-- ============================================================
--  MOAZZIZ Movie Recommender  –  MySQL Setup Script
--  Run this once before starting the app, OR let database.py
--  auto-create everything on first launch.
-- ============================================================

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS moazziz_movies
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE moazziz_movies;

-- 2. Users table
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80)  UNIQUE NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,          -- bcrypt hash, never plain text
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Watch history  (every time a user runs "Recommend" on a movie)
CREATE TABLE IF NOT EXISTS watch_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    movie_title VARCHAR(255) NOT NULL,
    watched_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. User favourites  (movies the user saves with ❤️)
CREATE TABLE IF NOT EXISTS user_favourites (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    movie_title VARCHAR(255) NOT NULL,
    added_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_fav (user_id, movie_title),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Optional: create a dedicated MySQL user instead of using root
-- CREATE USER 'moazziz_user'@'localhost' IDENTIFIED BY 'strong_password';
-- GRANT ALL PRIVILEGES ON moazziz_movies.* TO 'moazziz_user'@'localhost';
-- FLUSH PRIVILEGES;
