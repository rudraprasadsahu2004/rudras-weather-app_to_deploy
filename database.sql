-- ============================================================
-- Rudra's Weather App v2 — XAMPP MySQL Database Schema
-- Run this in phpMyAdmin or MySQL CLI
-- ============================================================

CREATE DATABASE IF NOT EXISTS rudras_weather CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE rudras_weather;

-- ── Search History ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS search_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    city        VARCHAR(100) NOT NULL,
    country     VARCHAR(100) DEFAULT '',
    latitude    DECIMAL(9,6) NOT NULL,
    longitude   DECIMAL(9,6) NOT NULL,
    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city),
    INDEX idx_searched_at (searched_at)
);

-- ── Weather Cache (10-min TTL) ───────────────────────────────
CREATE TABLE IF NOT EXISTS weather_cache (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    cache_key       VARCHAR(50) NOT NULL UNIQUE,   -- "lat_lon" rounded to 2dp
    city            VARCHAR(100) NOT NULL,
    country         VARCHAR(100) DEFAULT '',
    temperature_c   DECIMAL(5,2),
    temperature_f   DECIMAL(5,2),
    feels_like_c    DECIMAL(5,2),
    humidity        INT,
    wind_speed_kmh  DECIMAL(6,2),
    condition_text  VARCHAR(100),
    condition_type  VARCHAR(30),
    weather_icon    VARCHAR(10),
    safety_level    VARCHAR(20),
    uv_index        DECIMAL(4,1),
    precautions     TEXT,                          -- JSON array stored as text
    forecast_json   LONGTEXT,                      -- 7-day forecast JSON
    hourly_json     LONGTEXT,                      -- 24-hour hourly JSON
    cached_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cache_key (cache_key),
    INDEX idx_cached_at (cached_at)
);

-- ── Pinned Cities ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pinned_cities (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    city        VARCHAR(100) NOT NULL,
    country     VARCHAR(100) DEFAULT '',
    latitude    DECIMAL(9,6) NOT NULL,
    longitude   DECIMAL(9,6) NOT NULL,
    pinned_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_city_coords (latitude, longitude)
);

-- ── Weather Alerts Log ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS weather_alerts (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    city         VARCHAR(100) NOT NULL,
    alert_type   VARCHAR(50) NOT NULL,   -- 'storm', 'extreme_heat', 'freeze', etc.
    alert_msg    TEXT,
    safety_level VARCHAR(20),
    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city),
    INDEX idx_triggered_at (triggered_at)
);

-- ── Sample pinned cities (optional) ─────────────────────────
INSERT IGNORE INTO pinned_cities (city, country, latitude, longitude) VALUES
  ('Mumbai',    'India',          19.0760,  72.8777),
  ('Chennai',   'India',          13.0827,  80.2707),
  ('New Delhi', 'India',          28.6139,  77.2090);
