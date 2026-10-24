-- TD2 Loot Advisor — topluluk düşüş istatistikleri (Cloudflare D1 / SQLite)
CREATE TABLE IF NOT EXISTS drops (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  day       TEXT NOT NULL,          -- YYYY-MM-DD (UTC)
  week      TEXT NOT NULL,          -- haftalık sıfırlamanın günü (Salı) YYYY-MM-DD
  activity  TEXT NOT NULL,
  kind      TEXT NOT NULL,
  slot      TEXT,
  name      TEXT,
  brand     TEXT,
  gear_set  TEXT,
  rarity    TEXT,
  attrs     TEXT,                   -- attribute anahtarları, virgülle (değer yok)
  best_q    INTEGER,                -- en iyi attribute'un rulo kalitesi % (0-100)
  client    TEXT NOT NULL,          -- istemci kimliğinin tuzlu özeti (geri çevrilemez)
  sig       TEXT NOT NULL,          -- eşya imzası özeti (aynı eşya aynı gün bir kez sayılır)
  created   INTEGER NOT NULL,
  UNIQUE (client, sig, day)
);
CREATE INDEX IF NOT EXISTS idx_drops_act_week ON drops (activity, week);
CREATE INDEX IF NOT EXISTS idx_drops_name ON drops (name);
CREATE INDEX IF NOT EXISTS idx_drops_week ON drops (week);

CREATE TABLE IF NOT EXISTS rate (
  bucket  TEXT NOT NULL,            -- 'c:'+istemci özeti ya da 'i:'+IP özeti
  hour    INTEGER NOT NULL,
  n       INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket, hour)
);
