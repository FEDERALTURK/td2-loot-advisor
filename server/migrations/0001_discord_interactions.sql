CREATE TABLE IF NOT EXISTS discord_interactions (
  interaction_id TEXT PRIMARY KEY,
  user_id        TEXT NOT NULL,
  created        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_discord_interactions_created ON discord_interactions (created);
CREATE TABLE IF NOT EXISTS discord_rate_limits (
  user_id      TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  requests     INTEGER NOT NULL,
  PRIMARY KEY (user_id, window_start)
);
