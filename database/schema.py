"""
OpenSearch by DeepLogic — Database Schema Definitions
Defines tables, B-tree indexes, FTS5 virtual table, and sync triggers.
"""

SCHEMA_SQL = """
-- Main Files and Folders table
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT UNIQUE NOT NULL,
    parent_path TEXT NOT NULL,
    extension TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    created_time REAL DEFAULT 0,
    modified_time REAL DEFAULT 0,
    accessed_time REAL DEFAULT 0,
    is_directory INTEGER DEFAULT 0,
    is_hidden INTEGER DEFAULT 0,
    is_system INTEGER DEFAULT 0,
    drive TEXT NOT NULL
);

-- Fast B-Tree Indexes for targeted filters and sorting
CREATE INDEX IF NOT EXISTS idx_files_name_nocase ON files(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension);
CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent_path);
CREATE INDEX IF NOT EXISTS idx_files_drive_dir ON files(drive, is_directory);
CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);
CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_time);

-- FTS5 Full-Text Search Virtual Table (External Content Table)
CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    name,
    path,
    content='files',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

-- Synchronization Triggers between files and files_fts
CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, name, path) VALUES (new.id, new.name, new.path);
END;

CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, name, path) VALUES('delete', old.id, old.name, old.path);
END;

CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, name, path) VALUES('delete', old.id, old.name, old.path);
    INSERT INTO files_fts(rowid, name, path) VALUES (new.id, new.name, new.path);
END;

-- Indexed Locations and Drive Metadata
CREATE TABLE IF NOT EXISTS locations_meta (
    location TEXT PRIMARY KEY,
    drive TEXT NOT NULL,
    total_files INTEGER DEFAULT 0,
    total_folders INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    last_scanned REAL DEFAULT 0
);
"""
