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
from repository import Repository

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
        query = f"SELECT * FROM websites WHERE website_id = {visit_id}"
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
        self.repository.save_site(url)
        result = self.repository.website_id
        if result > 0:
            return {
                "success": "Site saved",
                "cached_media": self.repository.stat_data["cached_media"],
                "website": self.repository.stat_data["website"],
                "known_from_before": self.repository.stat_data["known_from_before"],
                "website_id": result,
                "visit_id": self.repository.visit_id
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
        query = f"SELECT q.*, v.url as website_url, v.base_website as base_website FROM queries as q JOIN websites as v ON v.website_id = q.website_id ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT q.*, v.url AS website_url, v.base_website AS base_website FROM queries AS q JOIN websites AS v ON v.website_id = q.website_id WHERE q.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_metadata(self, page: int = 0, limit: int = 10, sort: str = "identifier", dir: str = "asc", website_id: int = 0):
        query = f"SELECT m.*, attr.description, attr.source_link, v.url, v.base_website FROM metadata as m LEFT JOIN attributes AS attr ON attr.attribute_id = m.attribute_id JOIN websites AS v ON v.website_id = m.website_id ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT m.*, attr.description, attr.source_link, v.url, v.base_website FROM metadata as m LEFT JOIN attributes AS attr ON attr.attribute_id = m.attribute_id JOIN websites AS v ON v.website_id = m.website_id WHERE m.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_visits(self, page: int = 0, limit: int = 10, sort: str = "url", dir: str = "asc"):
        query = f"SELECT * FROM visists AS v ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_websites(self, page: int = 0, limit: int = 10, sort: str = "url", dir: str = "asc", only_visited: bool = False):
        query = f"SELECT v.*,GROUP_CONCAT(t.tag) AS tags FROM websites AS v LEFT JOIN tags AS t ON t.website_id = v.website_id GROUP BY  v.url ORDER BY v.{sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if only_visited:
            query = f"SELECT v.*,GROUP_CONCAT(t.tag) AS tags FROM websites AS v LEFT JOIN tags AS t ON t.website_id = v.website_id WHERE v.actually_visited = 1 GROUP BY v.url ORDER BY v.{sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        paging = Paging(page=page, limit=limit, sort=sort, dir=dir)
        query = "SELECT COUNT(*) FROM websites"
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
        query = f"SELECT c.*, v.url, v.base_website FROM comments as c JOIN websites AS v ON v.website_id = c.website_id ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT c.*, v.url, v.base_website FROM comments AS c JOIN websites AS v ON v.website_id = c.website_id WHERE c.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
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
        query = f"SELECT * FROM websites WHERE url like '%{query_str}%'"
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
        result["lifetime"]["websites"] = self.get_count("websites")
        result["lifetime"]["metadata"] = self.get_count("metadata")
        result["lifetime"]["tags"] = self.get_count("tags")
        result["lifetime"]["media"] = self.get_count("media")
        result["lifetime"]["website_media_ratio"] = result["lifetime"]["media"] / result["lifetime"]["websites"]
        result["lifetime"]["website_metadata_ratio"] = result["lifetime"]["metadata"] / result["lifetime"]["websites"]

        result["monthly"]["website_metadata_ratio"] = result["monthly"]["metadata"] / result["monthly"]["websites"]
        result["monthly"]["websites"] = self.get_count("websites", "WHERE date > datetime('now', '-1 month')")
        result["monthly"]["media"] = self.get_count("media", "WHERE date > datetime('now', '-1 month')")
        result["monthly"]["website_media_ratio"] = result["monthly"]["media"] / result["monthly"]["websites"]
        result["monthly"]["metadata"] = self.get_count("metadata", "WHERE date > datetime('now', '-1 month')")
        result["monthly"]["tags"] = self.get_count("tags", "WHERE date > datetime('now', '-1 month')")
    
        result["daily"]["websites"] = self.get_count("websites", "WHERE date > datetime('now', '-1 day')")
        result["daily"]["metadata"] = self.get_count("metadata", "WHERE date > datetime('now', '-1 day')")
        result["daily"]["website_metadata_ratio"] = result["daily"]["metadata"] / result["daily"]["websites"]
        result["daily"]["media"] = self.get_count("media", "WHERE date > datetime('now', '-1 day')")
        result["daily"]["website_media_ratio"] = result["daily"]["media"] / result["daily"]["websites"]
        result["daily"]["tags"] = self.get_count("tags", "WHERE date > datetime('now', '-1 day')")

        return result

    def get_count(self, table:str = "", where:str = ""):
        query = f"SELECT COUNT(*) FROM {table} {where}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchone()[0]


if __name__ == "__main__":
    con = sqlite3.connect(config["write_database"])
    cursor = con.cursor()
    arguments=sys.argv

    setup_db(cursor, con)
    fill_metadata_descriptions(cursor, con)
    con.commit()
    con.close()

    repository = Repository(config["write_database"], config["read_database"])

    if "link" in arguments[1] :
        urlsToCheck = arguments[2:]
    elif "file" in arguments[1]:
        with open(arguments[2], "r") as file:
            urlsToCheck = file.readlines()
            if "|" in urlsToCheck[0]:
                urlsToCheck = [x.split("|")[0] for x in urlsToCheck]
    for url in urlsToCheck:
        originalUrl = url
        checkedUrl = check_url(url)
        if not checkedUrl:
            print("Invalid URL: "+url)
            continue
        url = checkedUrl
        print("Attempting to scan: "+url)
        repository.save_site(url, originalUrl)
        print(repository.stat_data)