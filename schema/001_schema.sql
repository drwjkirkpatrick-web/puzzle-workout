-- fun-problem-26 question bank schema.
-- The database is BUILT ARTIFACT: regenerate it with scripts/build_db.py.

CREATE TABLE IF NOT EXISTS questions (
    id              TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    difficulty      INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    question        TEXT NOT NULL,
    guidance        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    alt_answers     TEXT NOT NULL DEFAULT '[]',
    explanation     TEXT NOT NULL,
    tags            TEXT NOT NULL DEFAULT '[]',
    source_kind     TEXT NOT NULL CHECK (source_kind IN ('original', 'public-domain', 'open-license')),
    source_title    TEXT NOT NULL,
    source_author   TEXT,
    source_year     INTEGER,
    source_url      TEXT,
    source_license  TEXT NOT NULL,
    source_accessed TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_questions_category   ON questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_source     ON questions(source_title);
