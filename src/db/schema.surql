DEFINE NAMESPACE IF NOT EXISTS tnved;
USE NS tnved;
DEFINE DATABASE IF NOT EXISTS main;
USE DB main;

-- Classifier tree
DEFINE TABLE IF NOT EXISTS codes SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS code       ON codes TYPE string ASSERT string::len($value) >= 2 AND string::len($value) <= 10;
DEFINE FIELD IF NOT EXISTS name_ru    ON codes TYPE string;
DEFINE FIELD IF NOT EXISTS parent     ON codes TYPE option<string>;
DEFINE FIELD IF NOT EXISTS level      ON codes TYPE int ASSERT $value IN [2,4,6,8,10];
DEFINE FIELD IF NOT EXISTS section    ON codes TYPE option<string>;
DEFINE FIELD IF NOT EXISTS group_code ON codes TYPE option<string>;
DEFINE FIELD IF NOT EXISTS unit       ON codes TYPE option<string>;
DEFINE INDEX IF NOT EXISTS idx_code   ON codes FIELDS code UNIQUE;
DEFINE INDEX IF NOT EXISTS idx_parent ON codes FIELDS parent;
DEFINE INDEX IF NOT EXISTS idx_group  ON codes FIELDS group_code;

-- Import duties
DEFINE TABLE IF NOT EXISTS duties SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS code             ON duties TYPE string;
DEFINE FIELD IF NOT EXISTS name_uz          ON duties TYPE string;
DEFINE FIELD IF NOT EXISTS duty_pct         ON duties TYPE option<float>;
DEFINE FIELD IF NOT EXISTS min_per_kg_usd   ON duties TYPE option<float>;
DEFINE FIELD IF NOT EXISTS min_per_unit_usd ON duties TYPE option<float>;
DEFINE FIELD IF NOT EXISTS min_per_liter_usd ON duties TYPE option<float>;
DEFINE FIELD IF NOT EXISTS raw_text_uz      ON duties TYPE string;
DEFINE INDEX IF NOT EXISTS idx_duty_code    ON duties FIELDS code UNIQUE;

-- Explanation chunks (RAG corpus)
DEFINE TABLE IF NOT EXISTS chunks SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS text          ON chunks TYPE string;
DEFINE FIELD IF NOT EXISTS primary_code  ON chunks TYPE option<string>;
DEFINE FIELD IF NOT EXISTS related_codes ON chunks TYPE array<string> DEFAULT [];
DEFINE FIELD IF NOT EXISTS page_num      ON chunks TYPE int;
DEFINE FIELD IF NOT EXISTS section       ON chunks TYPE option<string>;
DEFINE FIELD IF NOT EXISTS group_code    ON chunks TYPE option<string>;
DEFINE FIELD IF NOT EXISTS embedding     ON chunks TYPE array<float>;
DEFINE INDEX IF NOT EXISTS idx_emb          ON chunks FIELDS embedding HNSW DIMENSION 1536 TYPE F32 DIST COSINE;
DEFINE INDEX IF NOT EXISTS idx_primary_code ON chunks FIELDS primary_code;

-- Users
DEFINE TABLE IF NOT EXISTS users SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS telegram_id  ON users TYPE int;
DEFINE FIELD IF NOT EXISTS language     ON users TYPE string ASSERT $value IN ["uz","ru","en"] DEFAULT "uz";
DEFINE FIELD IF NOT EXISTS username     ON users TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created_at   ON users TYPE datetime DEFAULT time::now();
DEFINE FIELD IF NOT EXISTS last_seen_at ON users TYPE datetime DEFAULT time::now();
DEFINE INDEX IF NOT EXISTS idx_tg       ON users FIELDS telegram_id UNIQUE;

-- Daily usage (rate limit)
DEFINE TABLE IF NOT EXISTS daily_usage SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS user  ON daily_usage TYPE record<users>;
DEFINE FIELD IF NOT EXISTS date  ON daily_usage TYPE string;
DEFINE FIELD IF NOT EXISTS count ON daily_usage TYPE int DEFAULT 0;
DEFINE INDEX IF NOT EXISTS idx_user_date ON daily_usage FIELDS user, date UNIQUE;

-- Query history
DEFINE TABLE IF NOT EXISTS query_logs SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS user            ON query_logs TYPE record<users>;
DEFINE FIELD IF NOT EXISTS query_text      ON query_logs TYPE string;
DEFINE FIELD IF NOT EXISTS query_type      ON query_logs TYPE string ASSERT $value IN ["text","photo","voice"];
DEFINE FIELD IF NOT EXISTS result_code     ON query_logs TYPE option<string>;
DEFINE FIELD IF NOT EXISTS result_name     ON query_logs TYPE option<string>;
DEFINE FIELD IF NOT EXISTS confidence      ON query_logs TYPE option<float>;
DEFINE FIELD IF NOT EXISTS response_time_ms ON query_logs TYPE int;
DEFINE FIELD IF NOT EXISTS created_at      ON query_logs TYPE datetime DEFAULT time::now();
DEFINE INDEX IF NOT EXISTS idx_user_time   ON query_logs FIELDS user, created_at;
