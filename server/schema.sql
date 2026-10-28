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

-- Hata raporları / istekler: GitHub'a iletilene kadar kuyruk, sonra issue numarası (durum sorgusu için)
CREATE TABLE IF NOT EXISTS reports (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  created  INTEGER NOT NULL,
  client   TEXT NOT NULL,          -- istemci kimliğinin tuzlu özeti
  payload  TEXT NOT NULL,          -- GitHub issue gövdesi (temizlenmiş)
  state    TEXT NOT NULL,          -- queued | sent
  number   INTEGER                 -- GitHub issue numarası
);
CREATE INDEX IF NOT EXISTS idx_reports_state ON reports (state);

-- ---------------------------------------------------------------- hesaplar ve lisanslar (accounts.js)
-- Hiçbir düz belirteç / anahtar / davet kodu saklanmaz: yalnız SHA-256 özetleri.
CREATE TABLE IF NOT EXISTS accounts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id  TEXT NOT NULL UNIQUE,
  username    TEXT NOT NULL,
  avatar      TEXT,
  created     INTEGER NOT NULL,
  last_login  INTEGER NOT NULL,
  banned      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS auth_pending (
  state       TEXT PRIMARY KEY,         -- istemcinin rastgele durumu
  challenge   TEXT NOT NULL,            -- SHA-256(verifier) — oturumu yalnız verifier sahibi alır
  created     INTEGER NOT NULL,
  done        INTEGER NOT NULL DEFAULT 0,
  account_id  INTEGER,
  error       TEXT,
  port        INTEGER NOT NULL DEFAULT 0,   -- programın yerel dönüş portu (127.0.0.1)
  grant_hash  TEXT                          -- Discord dönüşünde yerel programa giden tek kullanımlık kanıt
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash  TEXT PRIMARY KEY,
  account_id  INTEGER NOT NULL,
  device_hash TEXT NOT NULL,             -- tuzlu cihaz özeti (lisans cihaz sınırı)
  device_pub  TEXT NOT NULL,             -- yetki belgesindeki cihaz özeti (program doğrular)
  created     INTEGER NOT NULL,
  expires     INTEGER NOT NULL,
  last_seen   INTEGER NOT NULL,
  revoked     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_acc ON sessions (account_id);
CREATE TABLE IF NOT EXISTS licenses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  key_hash      TEXT NOT NULL UNIQUE,
  key_hint      TEXT NOT NULL,          -- son 4 karakter (panelde tanımak için)
  tier          TEXT NOT NULL,
  created       INTEGER NOT NULL,
  duration_days INTEGER,                -- kullanılınca başlayan süre (NULL = süresiz)
  expires       INTEGER,
  account_id    INTEGER,
  redeemed      INTEGER,
  max_devices   INTEGER NOT NULL DEFAULT 1,
  source        TEXT NOT NULL,          -- admin | invite | gumroad
  source_ref    TEXT,
  note          TEXT,
  revoked       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_licenses_acc ON licenses (account_id);
CREATE INDEX IF NOT EXISTS idx_licenses_src ON licenses (source, source_ref);
CREATE TABLE IF NOT EXISTS devices (
  license_id  INTEGER NOT NULL,
  device_hash TEXT NOT NULL,
  first_seen  INTEGER NOT NULL,
  last_seen   INTEGER NOT NULL,
  PRIMARY KEY (license_id, device_hash)
);
CREATE TABLE IF NOT EXISTS invites (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  code_hash     TEXT NOT NULL UNIQUE,
  code_hint     TEXT NOT NULL,
  tier          TEXT NOT NULL,
  duration_days INTEGER,
  uses_left     INTEGER NOT NULL,
  expires       INTEGER,
  created       INTEGER NOT NULL,
  note          TEXT,
  revoked       INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS audit (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  t       INTEGER NOT NULL,
  actor   TEXT NOT NULL,
  action  TEXT NOT NULL,
  detail  TEXT
);
