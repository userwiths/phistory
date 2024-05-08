import sqlite3
import sys
import pdb

from urllib import parse
from urllib.request import Request,urlopen as uReq

from bs4 import BeautifulSoup

import json
from datetime import datetime

# Custom local files.
from config import config
from repository import Existance
from models import *

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
            website_id INTEGER,
            attribute_name,
            attribute_id INTEGER,
            identifier,
            identifier_name,
            attribute,
            attribute_value,
            date,
            FOREIGN KEY(website_id) REFERENCES visits(website_id)
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
            website_id INTEGER,
            media_link TEXT,
            alt_text TEXT,
            is_cached BOOLEAN DEFAULT FALSE,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(website_id) REFERENCES visits(website_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        tracking(
            website_id INTEGER,
            uses_google_tag_manager BOOLEAN DEFAULT FALSE,
            uses_facebook_pixel BOOLEAN DEFAULT FALSE,
            uses_google_analytics BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(website_id) REFERENCES visits(website_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        links(
            website_id INTEGER,
            destination_id INTEGER,
            link TEXT,
            destination TEXT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(website_id) REFERENCES visits(website_id)
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
            FOREIGN KEY(website_id) REFERENCES visits(website_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        comments(
            website_id INTEGER,
            query_id INTEGER,
            comment TEXT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(website_id) REFERENCES visits(website_id)
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
        cursor.execute("SELECT * FROM attributes WHERE description=?", (descriptions[key]["description"],))
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

class Manager:
    def __init__(self):
        self.repository = Repository(config["write_database"], config["read_database"])

    def get_user(self, user_id: int):
        query = "SELECT * FROM users WHERE user_id = ?"
        self.repository.read_cursor.execute(query, (user_id,))
        result = self.repository.read_cursor.fetchone()
        return result

    def get_users(self, page: int = 0, limit: int = 10, sort: str = "name", dir: str = "asc"):
        query = f"SELECT * FROM users ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        return result

    def post_user(self, username: str, password: str):
        query = "INSERT INTO users(username, password) VALUES (?,?)"
        self.repository.write_cursor.execute(query, (username, password))
        user_id = self.repository.write_cursor.lastrowid
        self.repository.write_connection.commit()
        return {"success": "User created", "user_id": user_id}

    def put_user(self, user_id: int, username: str, password: str, group_id: int):
        query = "UPDATE users SET username=?, password=? WHERE user_id=?"
        self.repository.write_cursor.execute(query, (username, password, user_id))
        tied_to_group = self.repository.read_cursor.execute("SELECT * FROM user_groups WHERE user_id=? AND group_id=?", (user_id, group_id))
        tied_to_group = tied_to_group.fetchall()
        if len(tied_to_group) == 0:
            query = "INSERT INTO user_groups(user_id, group_id) VALUES (?,?)"
            self.repository.write_cursor.execute(query, (user_id, group_id))
        self.repository.write_connection.commit()
        return {"success": "User updated"}

    def delete_user(self, user_id: int):
        query = "DELETE FROM users WHERE user_id=?"
        self.repository.write_cursor.execute(query, (user_id,))
        self.repository.write_connection.commit()
        return {"success": "User deleted"}

    def delete_user_group(self, user_id: int, group_id: int):
        query = "DELETE FROM user_groups WHERE user_id=? AND group_id=?"
        self.repository.write_cursor.execute(query, (user_id, group_id))
        self.repository.write_connection.commit()
        return {"success": "User group deleted"}

    def get_group(self, group_id: int):
        query = "SELECT * FROM groups WHERE group_id = ?"
        self.repository.read_cursor.execute(query, (group_id,))
        result = self.repository.read_cursor.fetchone()
        return result

    def get_groups(self, page: int = 0, limit: int = 10, sort: str = "name", dir: str = "asc"):
        query = f"SELECT * FROM groups ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        return result

    def post_group(self, name: str):
        query = "INSERT INTO groups(group_name) VALUES (?)"
        self.repository.write_cursor.execute(query, (name,))
        group_id = self.repository.write_cursor.lastrowid
        self.repository.write_connection.commit()
        return {"success": "Group created", "group_id": group_id}

    def get_current_user(self):
        return self.get_user(1)

    def get_visit(self, visit_id: int):
        query = f"SELECT * FROM visits WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchone()

        if result is None:
            return {"error": "Visit not found"}
        result = Website(website_id=result[0], url=result[1], base_website=result[2], times_visited=result[3], last_visit=result[4], actually_visited=result[5] == 1)

        query = f"SELECT * FROM media WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        media = self.repository.read_cursor.fetchall()
        for i in range(len(media)):
            result.media.append(Media(website_id=media[i][0], media_link=media[i][1], alt_text=media[i][2], is_cached=media[i][3], date=media[i][4]))

        links = []
        query = f"SELECT * FROM links WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        links = self.repository.read_cursor.fetchall()
        for i in range(len(links)):
            result.links.append(Link(website_id=links[i][0], destination_id=links[i][1], link=links[i][2], destination=links[i][3]))

        metadata = {}
        query = f"SELECT * FROM metadata WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        metadata = self.repository.read_cursor.fetchall()
        for i in range(len(metadata)):
            result.metadata.append(Metadata(website_id=metadata[i][0], attribute_name=metadata[i][1], attribute_id=metadata[i][2], identifier=metadata[i][3], identifier_name=metadata[i][4], attribute=metadata[i][5], attribute_value=metadata[i][6], date=metadata[i][7]))

        queries = []
        query = f"SELECT * FROM queries WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        queries = self.repository.read_cursor.fetchall()
        for i in range(len(queries)):
            result.queries.append(Query(website_id=queries[i][0], query=queries[i][1]))

        tags = []
        query = f"SELECT * FROM tags WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        tags = self.repository.read_cursor.fetchall()
        for i in range(len(tags)):
            result.tags.append(Tag(website_id=tags[i][0], query_id=tags[i][1], tag=tags[i][2], date=tags[i][3]))

        comments = []
        query = f"SELECT * FROM comments WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        comments = self.repository.read_cursor.fetchall()
        for i in range(len(comments)):
            result.comments.append(Comment(website_id=comments[i][0], query_id=comments[i][1], comment=comments[i][2], date=comments[i][3]))

        return result
    
    def post_visit(self, url: str):
        result = self.repository.save_site(url)
        if result > 0:
            return {
                "success": "Site saved",
                "cached_media": self.repository.stat_data["cached_media"],
                "website": self.repository.stat_data["website"],
                "known_from_before": self.repository.stat_data["known_from_before"],
                "id": result
            }
        return {"error": "Site not saved"}

    def put_visit(self, visit_id: int, comment: str = "", tag: str = ""):
        comment_id = 0
        tag_id = 0
        if len(comment) > 0:
            query = f"INSERT INTO comments(website_id, query_id, comment) VALUES ({visit_id}, null, '{comment}')"
            exists = self.repository.read_cursor.execute("SELECT * FROM comments WHERE website_id=? AND comment=?", (visit_id, comment))
            exists = exists.fetchall()
            if len(exists) == 0:
                self.repository.write_cursor.execute(query)
                comment_id = self.repository.write_cursor.lastrowid
        if len(tag) > 0:
            query = f"INSERT INTO tags(website_id, query_id, tag) VALUES ({visit_id}, null, '{tag}')"
            exists = self.repository.read_cursor.execute("SELECT * FROM tags WHERE website_id=? AND tag=?", (visit_id, tag))
            exists = exists.fetchall()
            if len(exists) == 0:
                self.repository.write_cursor.execute(query)
                tag_id = self.repository.write_cursor.lastrowid
        self.repository.write_connection.commit()
        message = "Comment and tag saved"
        if comment is None:
            message = "Tag saved"
        if tag is None:
            message = "Comment saved"
        return {"success": message, "comment_id": comment_id, "tag_id": tag_id}

    def get_queries(self, page: int = 0, limit: int = 10, sort: str = "query", dir: str = "asc", website_id:int = 0):
        query = f"SELECT q.*, v.url as website_url, v.base_website as base_website FROM queries as q JOIN visits as v ON v.website_id = q.website_id ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT q.*, v.url AS website_url, v.base_website AS base_website FROM queries AS q JOIN visits AS v ON v.website_id = q.website_id WHERE q.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_metadata(self, page: int = 0, limit: int = 10, sort: str = "identifier", dir: str = "asc", website_id: int = 0):
        query = f"SELECT m.*, attr.description, attr.source_link, v.url, v.base_website FROM metadata as m LEFT JOIN attributes AS attr ON attr.attribute_id = m.attribute_id JOIN visits AS v ON v.website_id = m.website_id ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT m.*, attr.description, attr.source_link, v.url, v.base_website FROM metadata as m LEFT JOIN attributes AS attr ON attr.attribute_id = m.attribute_id JOIN visits AS v ON v.website_id = m.website_id WHERE m.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_visits(self, page: int = 0, limit: int = 10, sort: str = "url", dir: str = "asc", only_visited: bool = False):
        query = f"SELECT v.*,GROUP_CONCAT(t.tag) AS tags FROM visits AS v LEFT JOIN tags AS t ON t.website_id = v.website_id GROUP BY  v.url ORDER BY v.{sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if only_visited:
            query = f"SELECT v.*,GROUP_CONCAT(t.tag) AS tags FROM visits AS v LEFT JOIN tags AS t ON t.website_id = v.website_id WHERE v.actually_visited = 1 GROUP BY v.url ORDER BY v.{sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        paging = Paging(page=page, limit=limit, sort=sort, dir=dir)
        query = "SELECT COUNT(*) FROM visits"
        self.repository.read_cursor.execute(query)
        total = self.repository.read_cursor.fetchone()[0]
        paging.total = total
        resultObject = WebsitePageResponse(paging=paging)
        for visit in result:
            tags_list = []
            if visit[6] is not None:
                tags_list = visit[6].split(",")
            for i in range(len(tags_list)):
                tags_list[i] = Tag(tag=tags_list[i], website_id=visit[0])
            resultObject.data.append(Website(website_id=visit[0], url=visit[1], base_website=visit[2], times_visited=visit[3], last_visit=visit[4], actually_visited=visit[5], tags = tags_list))
        return resultObject

    def get_tags(self, page: int = 0, limit: int = 10, sort: str = "tag", dir: str = "asc", website_id: int = 0):
        query = f"SELECT * FROM tags as t ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT * FROM tags as t WHERE t.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_comments(self, page: int = 0, limit: int = 10, sort: str = "comment", dir: str = "asc", website_id :int = 0):
        query = f"SELECT c.*, v.url, v.base_website FROM comments as c JOIN visits AS v ON v.website_id = c.website_id ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT c.*, v.url, v.base_website FROM comments AS c JOIN visits AS v ON v.website_id = c.website_id WHERE c.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def search(self, query_str: str):
        resultObject = {
            "websites": [],
            "queries": [],
            "media": [],
            "links": [],
            "comments": [],
            "tags": []
        }
        query = f"SELECT * FROM visits WHERE url like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["websites"] = result
        
        query = f"SELECT * FROM queries WHERE query like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["queries"] = result

        query = f"SELECT * FROM media WHERE media_link like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["media"] = result
        
        query = f"SELECT * FROM comments WHERE comment like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["comments"] = result
        
        query = f"SELECT * FROM tags WHERE tag like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["tags"] = result

        query = f"SELECT * FROM links WHERE link like '%{query_str}%' OR destination like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["links"] = result
        
        return resultObject

    def construct_dashboard(self):
        result = {
            "lifetime": {},
            "monthly": {},
            "daily": {}
        }
        query = "SELECT COUNT(*) FROM visits"
        self.repository.read_cursor.execute(query)
        result["lifetime"]["visits"] = self.repository.read_cursor.fetchone()[0]

        query = "SELECT COUNT(*) FROM visits WHERE last_visit > datetime('now', '-1 month')"
        self.repository.read_cursor.execute(query)
        result["monthly"]["visits"] = self.repository.read_cursor.fetchone()[0]

        query = "SELECT COUNT(*) FROM visits WHERE last_visit > datetime('now', '-1 day')"
        self.repository.read_cursor.execute(query)
        result["daily"]["visits"] = self.repository.read_cursor.fetchone()[0]

        query = "SELECT COUNT(*) FROM metadata"
        self.repository.read_cursor.execute(query)
        result["lifetime"]["metadata"] = self.repository.read_cursor.fetchone()[0]
        result["lifetime"]["website_metadata_ratio"] = result["lifetime"]["metadata"] / result["lifetime"]["visits"]

        query = "SELECT COUNT(*) FROM metadata WHERE date > datetime('now', '-1 month')"
        self.repository.read_cursor.execute(query)
        result["monthly"]["metadata"] = self.repository.read_cursor.fetchone()[0]
        result["monthly"]["website_metadata_ratio"] = result["monthly"]["metadata"] / result["monthly"]["visits"]

        query = "SELECT COUNT(*) FROM metadata WHERE date > datetime('now', '-1 day')"
        self.repository.read_cursor.execute(query)
        result["daily"]["metadata"] = self.repository.read_cursor.fetchone()[0]
        result["daily"]["website_metadata_ratio"] = result["daily"]["metadata"] / result["daily"]["visits"]

        query = "SELECT COUNT(*) FROM media"
        self.repository.read_cursor.execute(query)
        result["lifetime"]["media"] = self.repository.read_cursor.fetchone()[0]
        result["lifetime"]["website_media_ratio"] = result["lifetime"]["media"] / result["lifetime"]["visits"]

        query = "SELECT COUNT(*) FROM media WHERE date > datetime('now', '-1 month')"
        self.repository.read_cursor.execute(query)
        result["monthly"]["media"] = self.repository.read_cursor.fetchone()[0]
        result["monthly"]["website_media_ratio"] = result["monthly"]["media"] / result["monthly"]["visits"]

        query = "SELECT COUNT(*) FROM media WHERE date > datetime('now', '-1 day')"
        self.repository.read_cursor.execute(query)
        result["daily"]["media"] = self.repository.read_cursor.fetchone()[0]
        result["daily"]["website_media_ratio"] = result["daily"]["media"] / result["daily"]["visits"]

        query = "SELECT COUNT(*) FROM tags"
        self.repository.read_cursor.execute(query)
        result["lifetime"]["tags"] = self.repository.read_cursor.fetchone()[0]

        query = "SELECT COUNT(*) FROM tags WHERE date > datetime('now', '-1 month')"
        self.repository.read_cursor.execute(query)
        result["monthly"]["tags"] = self.repository.read_cursor.fetchone()[0]

        query = "SELECT COUNT(*) FROM tags WHERE date > datetime('now', '-1 day')"
        self.repository.read_cursor.execute(query)
        result["daily"]["tags"] = self.repository.read_cursor.fetchone()[0]

        return result

class Repository:
    def __init__(self, write_db, read_db):
        self.write_connection = sqlite3.connect(write_db)
        self.write_cursor = self.write_connection.cursor()
        self.read_connection = sqlite3.connect(read_db)
        self.read_cursor = self.read_connection.cursor()
        self.stat_data = {
            "website": "",
            "known_from_before": False,
            "cached_media": 0
        }
        self.soup = BeautifulSoup()

    """
    Commits and closes connection to database on class destroy.
    """
    def __del__(self):
        self.write_connection.commit()
        self.write_connection.close()
        self.read_connection.close()

    """
    Gets all websites.
    :param is_main: True if main website, False if subpage, None if all.
    :type is_main: bool|None
    :return: List of websites.
    """
    def get_all_sites(self, is_main: bool|None = None):
        query = "SELECT * FROM visits"
        if is_main is False:
            query = "SELECT * FROM visits WHERE base_website IS NOT NULL"
        elif is_main is True:
            query = "SELECT * FROM visits WHERE base_website IS NULL"
        self.read_cursor.execute(query)
        return self.read_cursor.fetchall()

    """
    Get the site by a given URL.
    :param url: URL of the website.
    :type url: str
    :param strict: True if strict URL matching, False if partial URL matching.
    :type strict: bool
    :return: List of websites.
    """
    def get_site_by_url(self, url: str, strict: bool = False):
        host = parse.urlparse(url).hostname
        url = check_url(url, host)
        if url == False:
            return []
        if not strict:
            url = parse.urlparse(url).hostname
            try:
                self.read_cursor.execute("SELECT * FROM visits WHERE url like ?", (url,))
            except Exception as e:
                print(url)
            return self.read_cursor.fetchall()
        if "www" in url or "//" in url:
            url = url.replace("www.", "")
            url = url.split("//")
            if len(url) > 1:
                self.read_cursor.execute("SELECT * FROM visits WHERE url like ?", (url[0] + "%" + url[1] +"%",))
            else:
                self.read_cursor.execute("SELECT * FROM visits WHERE url like ?", (url[0]+"%",))
        else:
            self.read_cursor.execute("SELECT * FROM visits WHERE url like ?", (url+"%",))

        result = self.read_cursor.fetchall()
        return result

    """
    Get site's metadata records
    :param website_id: ID of the website.
    :type website_id: int
    """
    def get_site_metadata(self, website_id:int):
        self.read_cursor.execute("SELECT * FROM metadata WHERE website_id=?", (website_id,))
        return self.read_cursor.fetchall()

    """
    In case we have data about a standart used metadata attribute, fetch it.
    :param attribute_id: ID of the attribute.
    :type attribute_id: int
    """
    def get_metadata_description(self, attribute_id:int):
        self.read_cursor.execute("SELECT * FROM attributes WHERE attribute_id=?", (attribute_id,))
        return self.read_cursor.fetchall()

    def get_site_by_id(self, id: int):
        self.read_cursor.execute("SELECT * FROM visits WHERE website_id=?", (id,))
        return self.read_cursor.fetchall()

    """
    Check if metadata already exists, if not, save it.
    :param website_id: ID of the website.
    :type website_id: int
    :param identifier: Identifier of the metadata.
    :type identifier: str
    :param identifier_name: Name of the identifier.
    :type identifier_name: str
    :param value_name: Name of the value.
    :type value_name: str
    :param value: Value of the metadata.
    :type value: str
    :return: True if metadata was saved, False if metadata already exists.
    """
    def save_metadata(self, website_id: int, identifier: str, identifier_name: str, value_name: str, value: str) -> bool:
        query = "INSERT INTO metadata(website_id,identifier,identifier_name,attribute, attribute_value,date) VALUES (?,?,?,?,?,?)"
        params = (website_id, identifier, identifier_name, value, )
        self.read_cursor.execute("SELECT * FROM metadata WHERE website_id=? AND identifier=? AND identifier_name=? AND ((attribute_value=? AND attribute=?) OR (attribute_value IS NULL AND attribute IS NULL))", (website_id, identifier, identifier_name, value, value_name))
        if len(self.read_cursor.fetchall()) != 0:
            return False
        params = (website_id, identifier, identifier_name, value_name, value, str(datetime.now()))
        self.write_cursor.execute(query, params)
        self.write_connection.commit()
        return True
    
    def get_website_media(self, website_id: int):
        self.read_cursor.execute("SELECT * FROM media WHERE website_id=?", (website_id,))
        return self.read_cursor.fetchall()

    def get_media_by_link(self, media_link: str):
        self.read_cursor.execute("SELECT * FROM media WHERE media_link=?", (media_link,))
        return self.read_cursor.fetchall()

    def save_media(self, website_id: int, media_link: str, alt_text: str, is_cached: False) -> bool:
        query = "INSERT INTO media(website_id,media_link,alt_text,is_cached) VALUES (?,?,?,?)"
        if "cache" in media_link:
            is_cached = True
        if is_cached:
            all_media = self.get_website_media(website_id)
            fileName = media_link.split("/")[-1]
            for media in all_media:
                if fileName in media[1]:
                    self.stat_data["cached_media"] += 1
                    return False
        params = (website_id, media_link, alt_text, is_cached)
        exists = self.get_media_by_link(media_link)
        if len(exists) > 0 and exists[0][0] == website_id:
            return False 
        self.write_cursor.execute(query, params)
        self.write_connection.commit()
        return True

    def import_media(self, id: int):
        media = self.soup.select('img,picture,video,audio,object,embed,source,track')
        for tag in media:
            if tag is None:
                continue
            entries = tag.attrs
            keys = list(entries.keys())
            alt_text = tag.get("alt")

            if "src" in keys:
                source = entries["src"]
            elif "href" in keys:
                source = entries["href"]
            elif "data" in keys:
                source = entries["data"]
            else:
                print("Unknown media type: "+str(tag))
                continue
            self.save_media(id, source, alt_text, False)

    def upsert_website(self, url: str, site: str = "", actially_visited:bool = False) -> int:
        if url is None or len(url) < 1:
            return None
        originalUrl = url
        local = self.get_site_by_url(url, True)
        if len(local) > 0:
            id = local[0][0]
            self.stat_data["website"] = local[0][1]
            self.stat_data["known_from_before"] = True
        else:
            url = check_url(url, site)
            if url == False:
                print (originalUrl, url)
            parted_url = parse.urlparse(url)
            if parted_url.hostname is None:
                print("Invalid URL: "+url)
                return 0
            base_website = parted_url.scheme + "://" + parted_url.hostname
            if base_website == url:
                base_website = None
            params=(url,base_website, actially_visited)
            query="INSERT INTO visits(url,base_website,actually_visited) VALUES (?,?,?)"
            self.write_cursor.execute(query, params)
            self.write_connection.commit()
            id = self.write_cursor.lastrowid
        self.save_queries(originalUrl, self.stat_data["website"])
        return id
    
    def import_metatags(self, id: int):
        metatags = self.soup.find_all('meta')
        title = self.soup.find('title')
        if title is not None:
            self.save_metadata(id, "title", title.string, None, None)
        for tag in metatags:
            entries = tag.attrs
            keys = list(entries.keys())
            if(len(keys) == 2):
                self.save_metadata(id, keys[0], entries[keys[0]], keys[1], entries[keys[1]])
            elif(len(keys) == 1):
                self.save_metadata(id, keys[0], entries[keys[0]], None, None)

    def import_tracking(self, id: int):
        uses_google_tag_manager = False
        uses_facebook_pixel = False
        uses_google_analytics = False
        all_scripts = self.soup.find_all('script')
        if all_scripts is None:
            return
        if len(all_scripts) == 0:
            return
        for script in self.soup.find_all('script'):
            if "googletagmanager" in script.string:
                uses_google_tag_manager = True
            if "facebook" in script.string:
                uses_facebook_pixel = True
            if "google-analytics" in script.string:
                uses_google_analytics = True
            query = "INSERT INTO tracking(website_id,uses_google_tag_manager,uses_facebook_pixel,uses_google_analytics) VALUES (?,?,?,?)"
            params = (id, uses_google_tag_manager, uses_facebook_pixel, uses_google_analytics)
            self.write_cursor.execute(query, params)

    def import_links(self, id: int):
        links = self.soup.find_all('a')
        site = self.get_site_by_id(id)
        site = site[0][1]

        for link in links:
            text = link.string
            destination = link.get("href")
            if destination is None:
                destination = link.get("data-href")
            if destination is None:
                destination = link.get("data-link")
            if destination is None:
                destination = link.get("data-src")
            if destination is None:
                destination = link.get("data-url")
            if destination is None:
                continue
            try:
                destination_id = self.get_site_by_url(destination)
                if len(destination_id) == 0:
                    destination_id = self.upsert_website(destination, site)
                else:
                    destination_id = destination_id[0][0]
            except Exception as e:
                destination_id = None
            if "?" in destination:
                self.save_queries(destination, site)
                destination = check_url(destination)

            params = (id, destination_id, text, destination)
            exists = self.read_cursor.execute("SELECT * FROM links WHERE website_id=? AND destination=?", (id, destination))
            exists = exists.fetchall()
            if len(exists) > 0:
                continue
            query = "INSERT INTO links(website_id,destination_id,link,destination) VALUES (?,?,?,?)"
            self.write_cursor.execute(query, params)
            self.write_connection.commit()

    def save_queries(self, url: str, site: str = "") -> bool:
        if "?" not in url:
            return False
        websiteUrl = check_url(url, site)
        if websiteUrl == False:
            return False
        websiteObject = self.get_site_by_url(websiteUrl, False)
        id = None
        if len(websiteObject) == 0:
            id = self.upsert_website(websiteUrl)
            websiteObject = self.get_site_by_id(id)
        if "?" in websiteUrl:
            websiteUrl = url.split("?")[0]
        url = url.split("?")[1]
        query = "INSERT INTO queries(website_id,query) VALUES (?,?)"
        params = (id, url)
        exists = self.read_cursor.execute("SELECT * FROM queries WHERE website_id=? AND query=?", (id, url))
        exists = exists.fetchall()
        if len(exists) > 0:
            return False
        self.write_cursor.execute(query, params)
        self.write_connection.commit()
        return True

    def save_site(self, url: str) -> int:
        self.stat_data = {
            "website": "",
            "known_from_before": False,
            "cached_media": 0
        }

        id = self.upsert_website(url, "", True)
        if id == 0 or id is None:
            return 0
        req=Request(url,headers={'User-Agent': config["user_agent"]})
        response = uReq(req)
        result = str(response.read().decode(response.headers.get_content_charset()))
        self.soup = BeautifulSoup(result, 'html.parser')

        self.import_media(id)
        self.import_metatags(id)
        self.import_links(id)
        return id
        #self.import_tracking(self.soup, id)
            

if __name__ == "__main__":
    con = sqlite3.connect(config["write_database"])
    cursor = con.cursor()
    arguments=sys.argv

    setup_db(cursor, con)
    fill_metadata_descriptions(cursor, con)
    con.commit()
    con.close()

    repository = Repository(config["write_database"], config["read_database"])

    for url in arguments[1:]:
        checkedUrl = check_url(url)
        if not checkedUrl:
            print("Invalid URL: "+url)
            continue
        url = checkedUrl
        print("Attempting to scan: "+url)

        repository.save_site(url)
        print(repository.stat_data)
