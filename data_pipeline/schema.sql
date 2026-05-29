-- Kumbh Monitor Database Schema
-- Optimized for SQLite

-- Core Articles Table
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    publish_date TEXT NOT NULL,          -- Stored in YYYY-MM-DD format
    headline TEXT NOT NULL,
    raw_body TEXT,                       -- Raw HTML/unstructured text content
    clean_body TEXT,                     -- Cleaned text, boilerplates stripped
    hash_signature TEXT UNIQUE,          -- MD5/SHA256 of cleaned body or headline to enforce deduplication
    status TEXT DEFAULT 'raw',           -- 'raw', 'cleaned', 'deduplicated', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Static Taxonomy Tables (Taxonomy-as-Data Architecture)

CREATE TABLE IF NOT EXISTS editions (
    id TEXT PRIMARY KEY,                 -- e.g., 'edition.nashik_2015'
    display_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    start_date TEXT,                     -- Event start YYYY-MM-DD
    end_date TEXT                        -- Event end YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS themes (
    id TEXT PRIMARY KEY,                 -- e.g., 'theme.roads_bridges'
    display_name TEXT NOT NULL,
    definition TEXT,
    cluster TEXT NOT NULL                -- e.g., 'Infrastructure'
);

CREATE TABLE IF NOT EXISTS event_types (
    id TEXT PRIMARY KEY,                 -- e.g., 'event_type.announcement'
    display_name TEXT NOT NULL,
    definition TEXT
);

CREATE TABLE IF NOT EXISTS stakeholders (
    id TEXT PRIMARY KEY,                 -- e.g., 'stakeholder.gov_centre'
    display_name TEXT NOT NULL,
    definition TEXT
);

CREATE TABLE IF NOT EXISTS places (
    id TEXT PRIMARY KEY,                 -- e.g., 'place.nashik.ramkund'
    place_name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    city TEXT NOT NULL,                  -- 'Nashik', 'Trimbakeshwar', 'Prayagraj'
    notes TEXT
);

CREATE TABLE IF NOT EXISTS outcomes (
    id TEXT PRIMARY KEY,                 -- e.g., 'outcome.public_health'
    display_name TEXT NOT NULL,
    definition TEXT
);

-- Taxonomy Join Tables (Supporting Multi-tag relationships)

CREATE TABLE IF NOT EXISTS article_themes (
    article_id INTEGER,
    theme_id TEXT,
    PRIMARY KEY (article_id, theme_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS article_stakeholders (
    article_id INTEGER,
    stakeholder_id TEXT,
    PRIMARY KEY (article_id, stakeholder_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS article_places (
    article_id INTEGER,
    place_id TEXT,
    PRIMARY KEY (article_id, place_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS article_outcomes (
    article_id INTEGER,
    outcome_id TEXT,
    PRIMARY KEY (article_id, outcome_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (outcome_id) REFERENCES outcomes(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS article_event_types (
    article_id INTEGER,
    event_type_id TEXT,
    PRIMARY KEY (article_id, event_type_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (event_type_id) REFERENCES event_types(id) ON DELETE RESTRICT
);

-- Information Quality / Misinformation Engine Table
CREATE TABLE IF NOT EXISTS information_quality (
    article_id INTEGER PRIMARY KEY,
    source_tier INTEGER CHECK (source_tier IN (1, 2, 3, 4)),
    claim_type TEXT CHECK (claim_type IN ('factual', 'opinion', 'rumor', 'satire', 'verified', 'mixed')),
    evidence_type TEXT CHECK (evidence_type IN ('official_data', 'eyewitness', 'expert_analysis', 'hearsay', 'image_video', 'unspecified')),
    corroboration_count_24h INTEGER DEFAULT 0,
    contested INTEGER CHECK (contested IN (0, 1)) DEFAULT 0,
    correction_status TEXT CHECK (correction_status IN ('current', 'corrected', 'retracted', 'disputed')) DEFAULT 'current',
    risk_score REAL DEFAULT 0.0,
    risk_band TEXT CHECK (risk_band IN ('low', 'medium', 'high', 'critical')) DEFAULT 'low',
    human_reviewed TEXT CHECK (human_reviewed IN ('unreviewed', 'confirmed_clean', 'confirmed_misinfo', 'disputed')) DEFAULT 'unreviewed',
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

-- Create Indexes for fast querying on the dashboard and by ML clustering
CREATE INDEX IF NOT EXISTS idx_articles_publish_date ON articles(publish_date);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_hash_signature ON articles(hash_signature);
