SCHEMA = """
CREATE TABLE IF NOT EXISTS proxies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ip          TEXT    NOT NULL,
    port        INTEGER NOT NULL,
    protocol    TEXT    NOT NULL DEFAULT 'socks5',
    source      TEXT    NOT NULL DEFAULT 'unknown',
    added_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_checked TEXT,
    is_alive    INTEGER NOT NULL DEFAULT 0,
    fail_count  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(ip, port)
);

CREATE INDEX IF NOT EXISTS idx_alive ON proxies(is_alive);
CREATE INDEX IF NOT EXISTS idx_protocol ON proxies(protocol);
"""
