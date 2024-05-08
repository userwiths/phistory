import sqlite3
from urllib import parse
from urllib.request import Request, urlopen as uReq
from bs4 import BeautifulSoup
from datetime import datetime
from config import config
from utils import check_url
import constants

class Existance:
    @staticmethod
    def exists(table: str, arguments: dict, cursor) -> bool:
        query = f"SELECT * FROM {table} WHERE "
        for key, value in arguments.items():
            query += f"{key} = % AND "
        query = query[:-4]
        cursor.execute(query, list(arguments.values()))
        return cursor.fetchone() is not None

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
        self.website_id = 0
        self.visit_id = 0
        self.soup = BeautifulSoup()

    """
    Commits and closes connection to database on class destroy.
    """
    def __del__(self):
        self.write_connection.commit()
        self.write_connection.close()
        self.read_connection.close()

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
        #if url == False:
        #    return []
        if strict:
            #url = host
            try:
                self.read_cursor.execute("SELECT w.* FROM " + WEBSITES + " WHERE w.url like ?", (url,))
            except Exception as e:
                print(url)
            return self.read_cursor.fetchall()
        if "www" in url or "//" in url:
            url = url.replace("www.", "")
            url = url.split("//")
            if len(url) > 1:
                self.read_cursor.execute("SELECT w.* FROM " + WEBSITES + " WHERE w.url like ?", (url[0] + "%" + url[1] +"%",))
            else:
                self.read_cursor.execute("SELECT w.* FROM " + WEBSITES + " WHERE w.url like ?", (url[0]+"%",))
        else:
            self.read_cursor.execute("SELECT w.* FROM " + WEBSITES + " WHERE w.url like ?", (url+"%",))
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
    def save_metadata(self, visit_id: int, identifier: str, identifier_name: str, value_name: str, value: str) -> bool:
        query = "INSERT INTO metadata(visit_id,identifier,identifier_name,attribute, attribute_value,date) VALUES (?,?,?,?,?,?)"
        params = (visit_id, identifier, identifier_name, value, )
        self.read_cursor.execute("SELECT m.* FROM " + METADATA + " WHERE m.visit_id=? AND m.identifier=? AND m.identifier_name=? AND ((m.attribute_value=? AND m.attribute=?) OR (m.attribute_value IS NULL AND m.attribute IS NULL))", (visit_id, identifier, identifier_name, value, value_name))
        if len(self.read_cursor.fetchall()) != 0:
            return False
        params = (visit_id, identifier, identifier_name, value_name, value, str(datetime.now()))
        self.write_cursor.execute(query, params)
        self.write_connection.commit()
        return True

    def get_media_by_link(self, media_link: str):
        self.read_cursor.execute("SELECT me.* FROM " + MEDIA + " WHERE me.media_link=?", (media_link,))
        return self.read_cursor.fetchall()

    def save_media(self, media_link: str, alt_text: str, is_cached: False) -> bool:
        query = "INSERT INTO media(visit_id,media_link,alt_text,is_cached) VALUES (?,?,?,?)"
        if "cache" in media_link:
            is_cached = True
        if is_cached:
            self.read_cursor.execute("SELECT me.* FROM " + MEDIA + " WHERE me.visit_id=?", (self.visit_id,))
            all_media = self.read_cursor.fetchall()
            fileName = media_link.split("/")[-1]
            for media in all_media:
                if fileName in media[1]:
                    self.stat_data["cached_media"] += 1
                    return False
        params = (self.visit_id, media_link, alt_text, is_cached)
        exists = self.get_media_by_link(media_link)
        if len(exists) > 0 and exists[0][0] == self.visit_id:
            return False 
        self.write_cursor.execute(query, params)
        self.write_connection.commit()
        return True

    def import_media(self):
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
            self.save_media(source, alt_text, False)

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
            try:
                query="INSERT INTO websites(url,base_website,actually_visited) VALUES (?,?,?)"
                self.write_cursor.execute(query, params)
                self.write_connection.commit()
            except Exception as e:
                print(params, local, url)
                return 0
            id = self.write_cursor.lastrowid
        self.save_queries(originalUrl, self.stat_data["website"])
        self.website_id = id
    
    def import_metatags(self):
        metatags = self.soup.find_all('meta')
        title = self.soup.find('title')
        if title is not None:
            self.save_metadata(self.visit_id, "title", title.string, None, None)
        for tag in metatags:
            entries = tag.attrs
            keys = list(entries.keys())
            if(len(keys) == 2):
                self.save_metadata(self.visit_id, keys[0], entries[keys[0]], keys[1], entries[keys[1]])
            elif(len(keys) == 1):
                self.save_metadata(self.visit_id, keys[0], entries[keys[0]], None, None)

    def import_tracking(self):
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
            params = (self.website_id, uses_google_tag_manager, uses_facebook_pixel, uses_google_analytics)
            self.write_cursor.execute(query, params)

    def import_links(self):
        links = self.soup.find_all('a')
        site = self.stat_data["website"]

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
                    self.upsert_website(destination, site)
                    destination_id = self.website_id
                else:
                    destination_id = destination_id[0][0]
            except Exception as e:
                destination_id = None
            if "?" in destination:
                self.save_queries(destination, site)
                destination = check_url(destination)

            params = (self.visit_id, destination_id, text, destination)
            exists = self.read_cursor.execute("SELECT l.* FROM " + LINKS + " WHERE l.visit_id=? AND l.destination=?", (self.visit_id, destination))
            exists = exists.fetchall()
            if len(exists) > 0:
                continue
            query = "INSERT INTO links(visit_id,destination_id,link,destination) VALUES (?,?,?,?)"
            self.write_cursor.execute(query, params)
            self.write_connection.commit()

    def save_queries(self, url: str, site: str = "") -> bool:
        if "?" not in url:
            return False
        url = url.split("?")[1]
        query = "INSERT INTO queries(website_id,query) VALUES (?,?)"
        params = (self.website_id, url)
        exists = self.read_cursor.execute("SELECT q.* FROM " + QUERIES + " WHERE q.website_id=? AND q.query=?", (self.website_id, url))
        exists = exists.fetchall()
        if len(exists) > 0:
            return False
        self.write_cursor.execute(query, params)
        self.write_connection.commit()
        return True

    def load_site(self, url: str):
        req=Request(url,headers={'User-Agent': config["user_agent"]})
        response = uReq(req)
        charset = response.headers.get_content_charset() or 'utf-8'
        result = str(response.read().decode(charset))
        self.soup = BeautifulSoup(result, 'html.parser')

    def save_visit(self, url: str, originalUrl: str = ""):
        query = "SELECT v.* FROM " + VISITS + " WHERE v.url=?"
        if originalUrl == "":
            originalUrl = url
        self.read_cursor.execute(query, (originalUrl,))
        visits = self.read_cursor.fetchall()
        if len(visits) == 0:
            query = "INSERT INTO visits(url) VALUES (?)"
            self.write_cursor.execute(query, (originalUrl,))
        else :
            query = "UPDATE visits SET times_visited=times_visited+1 WHERE url=?"
            self.write_cursor.execute(query, (originalUrl,))
        self.write_connection.commit()
        id = self.write_cursor.lastrowid
        if id == 0:
            id = visits[0][0]
        self.visit_id = id

    def save_site(self, url: str, originalUrl: str = ""):
        self.stat_data = {
            "website": "",
            "known_from_before": False,
            "cached_media": 0
        }

        self.save_visit(originalUrl)
        self.load_site(originalUrl)

        self.import_media()
        self.import_metatags()
        self.import_links()