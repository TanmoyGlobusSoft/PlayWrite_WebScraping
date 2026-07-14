import sqlite3

conn = sqlite3.connect("meta_ads.db")
cursor = conn.cursor()


def save_to_db(data):

    # ---------- Ads ----------
    cursor.execute("""
        INSERT OR IGNORE INTO ads
        (library_id, brand, status, started_date, landing_domain)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["Library ID"],
        data["Brand"],
        data["Status"],
        data["Started Date"],
        data["Landing Domain"]
    ))

    conn.commit()

    # Current ad id
    cursor.execute(
        "SELECT id FROM ads WHERE library_id=?",
        (data["Library ID"],)
    )

    ad_id = cursor.fetchone()[0]

    # ---------- Platforms ----------
    cursor.execute(
        "DELETE FROM platforms WHERE ad_id=?",
        (ad_id,)
    )

    for platform in data["Platforms"]:

        cursor.execute("""
            INSERT INTO platforms
            (ad_id, platform)
            VALUES (?, ?)
        """, (
            ad_id,
            platform
        ))

    # ---------- Transparency ----------
    cursor.execute(
        "DELETE FROM transparency WHERE ad_id=?",
        (ad_id,)
    )

    if data["Transparency"]["Available"]:

        for region, value in data["Transparency"]["Regions"].items():

            for row in value["Audience"]:

                cursor.execute("""
                    INSERT INTO transparency
                    (ad_id, region, location, age, gender, reach)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (

                    ad_id,

                    region,

                    row["Location"],

                    row["Age"],

                    row["Gender"],

                    row["Reach"]

                ))

    conn.commit()