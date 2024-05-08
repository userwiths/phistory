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
import constants
import utils

class Manager:
    def __init__(self):
        self.repository = Repository(config["write_database"], config["read_database"])

    def get_user(self, user_id: int):
        query = "SELECT u.* FROM " + USERS + " WHERE u.user_id = ?"
        self.repository.read_cursor.execute(query, (user_id,))
        result = self.repository.read_cursor.fetchone()
        return result

    def get_users(self, page: int = 0, limit: int = 10, sort: str = "name", dir: str = "asc"):
        query = f"SELECT * FROM " + USERS + " ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
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
        tied_to_group = self.repository.read_cursor.execute("SELECT * FROM " + USER_GROUPS + " WHERE user_id=? AND group_id=?", (user_id, group_id))
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
        query = "SELECT * FROM " + GROUPS + " WHERE group_id = ?"
        self.repository.read_cursor.execute(query, (group_id,))
        result = self.repository.read_cursor.fetchone()
        return result

    def get_groups(self, page: int = 0, limit: int = 10, sort: str = "name", dir: str = "asc"):
        query = f"SELECT * FROM " + GROUPS + " ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
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

        query = f"SELECT * FROM " + MEDIA + " WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        media = self.repository.read_cursor.fetchall()
        for i in range(len(media)):
            result.media.append(Media(website_id=media[i][0], media_link=media[i][1], alt_text=media[i][2], is_cached=media[i][3], date=media[i][4]))

        links = []
        query = f"SELECT * FROM " + LINKS + " WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        links = self.repository.read_cursor.fetchall()
        for i in range(len(links)):
            result.links.append(Link(website_id=links[i][0], destination_id=links[i][1], link=links[i][2], destination=links[i][3]))

        metadata = {}
        query = f"SELECT * FROM " + METADATA + " WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        metadata = self.repository.read_cursor.fetchall()
        for i in range(len(metadata)):
            result.metadata.append(Metadata(website_id=metadata[i][0], attribute_name=metadata[i][1], attribute_id=metadata[i][2], identifier=metadata[i][3], identifier_name=metadata[i][4], attribute=metadata[i][5], attribute_value=metadata[i][6], date=metadata[i][7]))

        queries = []
        query = f"SELECT * FROM " + QUERIES + " WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        queries = self.repository.read_cursor.fetchall()
        for i in range(len(queries)):
            result.queries.append(Query(website_id=queries[i][0], query=queries[i][1]))

        tags = []
        query = f"SELECT * FROM " + TAGS + " WHERE website_id = {visit_id}"
        self.repository.read_cursor.execute(query)
        tags = self.repository.read_cursor.fetchall()
        for i in range(len(tags)):
            result.tags.append(Tag(website_id=tags[i][0], query_id=tags[i][1], tag=tags[i][2], date=tags[i][3]))

        comments = []
        query = f"SELECT * FROM  " + COMMENTS + " WHERE website_id = {visit_id}"
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
            exists = self.repository.read_cursor.execute("SELECT * FROM " + COMMENTS + " WHERE website_id=? AND comment=?", (visit_id, comment))
            exists = exists.fetchall()
            if len(exists) == 0:
                self.repository.write_cursor.execute(query)
                comment_id = self.repository.write_cursor.lastrowid
        if len(tag) > 0:
            query = f"INSERT INTO tags(website_id, query_id, tag) VALUES ({visit_id}, null, '{tag}')"
            exists = self.repository.read_cursor.execute("SELECT * FROM " + TAGS + " WHERE website_id=? AND tag=?", (visit_id, tag))
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
        query = f"SELECT q.*, w.url as website_url, w.base_website as base_website FROM " + QUERIES + " JOIN " + WEBSITES + " ON " + WEBSITE_TO_QUERY + " ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT q.*, w.url AS website_url, w.base_website AS base_website FROM " + QUERIES + " JOIN " + WEBSITES + " ON + " + WEBSITE_TO_QUERY + " WHERE q.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_metadata(self, page: int = 0, limit: int = 10, sort: str = "identifier", dir: str = "asc", visit_id: int = 0):
        query = f"SELECT m.*, a.description, a.source_link, v.url FROM " + METADATA + " LEFT JOIN " + ATTRIBUTES + " ON " + ATTRIBUTE_TO_METADATA + " JOIN " + VISITS + " ON " + VISIT_TO_METADATA + " ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT m.*, a.description, a.source_link, v.url FROM " + METADATA + " LEFT JOIN " + ATTRIBUTES + " ON " + ATTRIBUTE_TO_METADATA + " JOIN " + VISITS + " ON " + VISIT_TO_METADATA + " WHERE m.visit_id = {visit_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        self.repository.read_cursor.execute(query)
        return self.repository.read_cursor.fetchall()

    def get_visits(self, page: int = 0, limit: int = 10, sort: str = "url", dir: str = "asc"):
        query = f"SELECT * FROM " + VISITS + " AS v ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
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
        query = f"SELECT * FROM " + TAGS + " ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
        if website_id > 0:
            query = f"SELECT * FROM " + TAGS + " as t WHERE t.website_id = {website_id} ORDER BY {sort} {dir} LIMIT {limit} OFFSET {page * limit}"
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
            "visits": [],
            "websites": [],
            "queries": [],
            "media": [],
            "links": [],
            "comments": [],
            "tags": []
        }
        query = f"SELECT * FROM " + WEBSITES + " WHERE url like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["websites"] = result

        query = f"SELECT v.* FROM " + VISITS + "  WHERE v.url like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["visits"] = result
        
        query = f"SELECT * FROM " + QUERIES + " WHERE query like '%{query_str}%'"
        self.repository.read_cursor.execute(query)
        result = self.repository.read_cursor.fetchall()
        if len(result) > 0:
            resultObject["queries"] = result

        query = f"SELECT * FROM " + MEDIA + " WHERE media_link like '%{query_str}%'"
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