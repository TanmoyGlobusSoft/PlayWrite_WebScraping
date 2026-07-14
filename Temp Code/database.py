import sqlite3

conn = sqlite3.connect("meta_ads.db")

cursor = conn.cursor()

# ---------------- ADS ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS ads (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    library_id TEXT UNIQUE,

    brand TEXT,

    status TEXT,

    started_date TEXT,

    landing_domain TEXT,

    cta TEXT,

    ad_text TEXT,

    headline TEXT,

    description TEXT,

    advertiser TEXT,

    search_keyword TEXT,

    country TEXT,

    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

# ---------------- PLATFORMS ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS platforms (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ad_id INTEGER,

    platform TEXT,

    FOREIGN KEY(ad_id) REFERENCES ads(id)

)
""")

# ---------------- TRANSPARENCY ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS transparency (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ad_id INTEGER,

    region TEXT,

    location TEXT,

    age TEXT,

    gender TEXT,

    reach INTEGER,

    FOREIGN KEY(ad_id) REFERENCES ads(id)

)
""")



conn.commit()
conn.close()

print("Database Created Successfully.")