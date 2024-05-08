import urllib.parse

import constants

def setup_db(cursor, connection):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        groups(
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        user_groups(
            user_id INTEGER,
            group_id INTEGER,
            viewed_by_anoymous BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(group_id) REFERENCES groups(group_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        group_visibility(
            looking_group_id INTEGER,
            visible_group_id INTEGER,
            hidden BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(looking_group_id) REFERENCES groups(group_id),
            FOREIGN KEY(visible_group_id) REFERENCES groups(group_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        hidden_tags(
            group_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY(group_id) REFERENCES groups(group_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        visits(
            visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            times_visited INTEGER DEFAULT 0,
            last_visit DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS 
        websites(
            website_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url,
            base_website,
            times_visited INTEGER DEFAULT 0,
            last_visit DATETIME DEFAULT CURRENT_TIMESTAMP,
            actually_visited BOOLEAN DEFAULT FALSE,
            UNIQUE(url)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS 
        metadata(
            visit_id INTEGER,
            attribute_name,
            attribute_id INTEGER,
            identifier,
            identifier_name,
            attribute,
            attribute_value,
            date,
            FOREIGN KEY(visit_id) REFERENCES visits(visit_id)
            FOREIGN KEY(attribute_id) REFERENCES attributes(attribute_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS 
        attributes(
            attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description,
            source_link
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        media(
            visit_id INTEGER,
            media_link TEXT,
            alt_text TEXT,
            is_cached BOOLEAN DEFAULT FALSE,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(visit_id) REFERENCES visits(visit_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        tracking(
            website_id INTEGER,
            uses_google_tag_manager BOOLEAN DEFAULT FALSE,
            uses_facebook_pixel BOOLEAN DEFAULT FALSE,
            uses_google_analytics BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(website_id) REFERENCES websites(website_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        links(
            visit_id INTEGER,
            destination_id INTEGER,
            link TEXT,
            destination TEXT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(visit_id) REFERENCES visits(visit_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        queries(
            website_id INTEGER,
            query TEXT
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        tags(
            website_id INTEGER,
            query_id INTEGER,
            tag TEXT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(website_id) REFERENCES websites(website_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        comments(
            website_id INTEGER,
            query_id INTEGER,
            comment TEXT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(website_id) REFERENCES websites(website_id)
        )""")
    
    connection.commit()

def fill_metadata_descriptions(cursor, connection):
    descriptions = {
        "og:title": {
            "description": "Open Graph title",
            "source_link": "https://ogp.me/"
        },
        "og:description": {
            "description": "Open Graph description",
            "source_link": "https://ogp.me/"
        },
        "og:image": {
            "description": "Open Graph image",
            "source_link": "https://ogp.me/"
        },
        "og:url": {
            "description": "Open Graph URL",
            "source_link": "https://ogp.me/"
        },
        "og:type": {
            "description": "Open Graph type",
            "source_link": "https://ogp.me/"
        },
        "og:site_name": {
            "description": "Open Graph site name",
            "source_link": "https://ogp.me/"
        },
        "og:locale": {
            "description": "Open Graph locale",
            "source_link": "https://ogp.me/"
        },
        "og:locale:alternate": {
            "description": "Open Graph alternate locale",
            "source_link": "https://ogp.me/"
        },
        "og:video": {
            "description": "Open Graph video",
            "source_link": "https://ogp.me/"
        },
        "og:audio": {
            "description": "Open Graph audio",
            "source_link": "https://ogp.me/"
        },
        "og:determiner": {
            "description": "Open Graph determiner",
            "source_link": "https://ogp.me/"
        },
        "og:image:secure_url": {
            "description": "Open Graph secure URL",
            "source_link": "https://ogp.me/"
        },
        "og:image:alt": {
            "description": "Open Graph image alt text",
            "source_link": "https://ogp.me/"
        },
        "viewport": {
            "description": "Viewport",
            "source_link": "https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta/name"
        }
    }
    for key in descriptions:
        cursor.execute("SELECT a.* FROM " + ATTRIBUTES + " WHERE a.description=?", (descriptions[key]["description"],))
        result = cursor.fetchall()
        if len(result) == 0:
            cursor.execute("INSERT INTO attributes(description,source_link) VALUES (?,?)", (descriptions[key]["description"], descriptions[key]["source_link"]))

def check_url(url: str, website: str = "") -> str|bool:
    if url is None:
        return False
    if url == "" or len(url) < 1:
        return False
    if website in url:
        website = ""
    prefix = "http://"
    if config["use_https"]:
        prefix = "https://"
    if prefix in website:
        prefix = website
        website = ""
    if not url.startswith("http"):
        if "//" in url or ":" in url:
            return False
        if not url.startswith(prefix):
            url = prefix + website + url
    if "?" in url:
        url = url.split("?")[0]
    return url
