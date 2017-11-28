"""
    tmdb.py --- Jen Plugin for accessing tmdb data
    Copyright (C) 2017, Midraal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


    Usage Examples:
    <dir>
      <title>TMDB Popular</title>
      <tmdb>movies/popular</tmdb>
    </dir>

    <dir>
      <title>TMDB Now Playing</title>
      <tmdb>movies/now_playing</tmdb>
    </dir>

    <dir>
      <title>TMDB Top Rated</title>
      <tmdb>movies/top_rated</tmdb>
    </dir>

    <dir>
      <title>TMDB Popular</title>
      <tmdb>tv/popular</tmdb>
    </dir>

    <dir>
      <title>TMDB Top Rated</title>
      <tmdb>tv/top_rated</tmdb>
    </dir>

    <dir>
      <title>TMDB Airing Today</title>
      <tmdb>tv/today</tmdb>
    </dir>
	
	<dir>
      <title>True Movies</title>
      <tmdb>list/39817</tmdb>
    </dir>

    <dir>
      <title>Mafia Movies</title>
      <tmdb>list/39818</tmdb>
    </dir>

    <dir>
      <title>Search TMDB</title>
      <tmdb>search</tmdb>
    </dir>
"""

import pickle
import time

import koding
import resources.lib.external.tmdbsimple as tmdbsimple
import xbmcaddon
from koding import route
from resources.lib.plugin import Plugin
from resources.lib.util.context import get_context_items
from resources.lib.util.xml import JenItem, JenList, display_list
from unidecode import unidecode


CACHE_TIME = 3600  # change to wanted cache time in seconds

addon_fanart = xbmcaddon.Addon().getAddonInfo('fanart')
addon_icon = xbmcaddon.Addon().getAddonInfo('icon')


class TMDB(Plugin):
    name = "tmdb"

    def process_item(self, item_xml):
        if "<tmdb>" in item_xml:
            item = JenItem(item_xml)
            result_item = {
                'label': item["title"],
                'icon': item.get("thumbnail", addon_icon),
                'fanart': item.get("fanart", addon_fanart),
                'mode': "tmdb",
                'url': item.get("tmdb", ""),
                'folder': True,
                'imdb': "0",
                'content': "files",
                'season': "0",
                'episode': "0",
                'info': {},
                'year': "0",
                'context': get_context_items(item),
                "summary": item.get("summary", None)
            }
            result_item["properties"] = {'fanart_image': result_item["fanart"]}
            result_item['fanart_small'] = result_item["fanart"]
            return result_item
        elif "tmdb_tv_show" in item_xml:
            item = JenItem(item_xml)
            url = item.get("link", ")").replace("tmdb_tv_show(", "")[:-1]
            result_item = {
                'label': item["title"],
                'icon': item["thumbnail"],
                'fanart': item.get("fanart", addon_fanart),
                'mode': "tmdb_tv_show",
                'url': "tmdb_id" + url,
                'folder': True,
                'content': "tvshows",
                'season': "0",
                'episode': "0",
                'info': {},
                "imdb": item.get("imdb", "0"),
                'year': item.get("year", ""),
                'context': get_context_items(item),
                "summary": item.get("summary", None)
            }
            result_item["properties"] = {'fanart_image': result_item["fanart"]}
            result_item['fanart_small'] = result_item["fanart"]
            return result_item
        elif "tmdb_season(" in item_xml:
            item = JenItem(item_xml)
            url = item.get("link", ")").replace("tmdb_season(", "")[:-1]
            season = url.split(",")[1]
            result_item = {
                'label': item["title"],
                'icon': item["thumbnail"],
                'fanart': item.get("fanart", addon_fanart),
                'mode': "tmdb_season",
                'url': "tmdb_id" + url,
                'folder': True,
                'content': "seasons",
                'season': str(season),
                'episode': "0",
                'info': {},
                "imdb": item.get("imdb", "0"),
                'year': item.get("year", ""),
                'context': {},
                "summary": item.get("summary", None)
            }
            result_item["properties"] = {'fanart_image': result_item["fanart"]}
            result_item['fanart_small'] = result_item["fanart"]
            return result_item


@route(mode='tmdb', args=["url"])
def tmdb(url):
    page = 1
    xml = fetch_from_db(url)
    if not xml:
        xml = ""
        response = None
        if url.startswith("movies"):
            if url.startswith("movies/popular"):
                last = url.split("/")[-1]
                if last.isdigit():
                    page = int(last)
                if not response:
                    response = tmdbsimple.Movies().popular(page=page)
            if url.startswith("movies/now_playing"):
                last = url.split("/")[-1]
                if last.isdigit():
                    page = int(last)
                if not response:
                    response = tmdbsimple.Movies().now_playing(page=page)
            if url.startswith("movies/top_rated"):
                last = url.split("/")[-1]
                if last.isdigit():
                    page = int(last)
                if not response:
                    response = tmdbsimple.Movies().top_rated(page=page)

            for item in response["results"]:
                xml += get_movie_xml(item)
        elif url.startswith("tv"):
            if url.startswith("tv/popular"):
                last = url.split("/")[-1]
                if last.isdigit():
                    page = int(last)
                if not response:
                    response = tmdbsimple.TV().popular(page=page)
            elif url.startswith("tv/top_rated"):
                last = url.split("/")[-1]
                if last.isdigit():
                    page = int(last)
                if not response:
                    response = tmdbsimple.TV().top_rated(page=page)
            elif url.startswith("tv/today"):
                last = url.split("/")[-1]
                if last.isdigit():
                    page = int(last)
                if not response:
                    response = tmdbsimple.TV().airing_today(page=page)
            for item in response["results"]:
                xml += get_show_xml(item)
        elif url.startswith("list"):
            list_id = url.split("/")[-1]
            if not response:
                response = tmdbsimple.Lists(list_id).info()
            for item in response["items"]:
                if "title" in item:
                    xml += get_movie_xml(item)
                elif "name" in item:
                    xml += get_show_xml(item)
        elif url.startswith("person"):
            split_url = url.split("/")
            person_id = split_url[-1]
            media = split_url[-2]
            if media == "movies":
                if not response:
                    response = tmdbsimple.People(person_id).movie_credits()
            elif media == "shows":
                if not response:
                    response = tmdbsimple.People(person_id).tv_credits()

            for job in response:
                if job == "id":
                    continue
                for item in response[job]:
                    if media == "movies":
                        xml += get_movie_xml(item)
                    elif media == "shows":
                        xml += get_show_xml(item)
        elif url.startswith("genre"):
            split_url = url.split("/")
            if len(split_url) == 3:
                url += "/1"
                split_url.append(1)
            page = int(split_url[-1])
            genre_id = split_url[-2]
            media = split_url[-3]
            if media == "movies":
                if not response:
                    response = tmdbsimple.Discover().movie(with_genres=genre_id,
                                                           page=page)
            elif media == "shows":
                if not response:
                    response = tmdbsimple.Discover().tv(with_genres=genre_id,
                                                        page=page)

            for item in response["results"]:
                if media == "movies":
                    xml += get_movie_xml(item)
                elif media == "shows":
                    xml += get_show_xml(item)
        elif url.startswith("keyword"):
            split_url = url.split("/")
            if len(split_url) == 3:
                url += "/1"
                split_url.append(1)
            page = int(split_url[-1])
            keyword_id = split_url[-2]
            media = split_url[-3]
            if media == "movies":
                if not response:
                    response = tmdbsimple.Discover().movie(with_keywords=keyword_id,
                                                           page=page)
            elif media == "shows":
                if not response:
                    response = tmdbsimple.Discover().tv(with_keywords=keyword_id,
                                                        page=page)

            for item in response["results"]:
                if media == "movies":
                    xml += get_movie_xml(item)
                elif media == "shows":
                    xml += get_show_xml(item)
        elif url.startswith("collection"):
            split_url = url.split("/")
            collection_id = split_url[-1]
            if not response:
                response = tmdbsimple.Collections(collection_id).info()

            for item in response["parts"]:
                xml += get_movie_xml(item)
        elif url.startswith("search"):
            if url == "search":
                term = koding.Keyboard("Search For")
                url = "search/%s" % term
            split_url = url.split("/")
            if len(split_url) == 2:
                url += "/1"
                split_url.append(1)
            page = int(split_url[-1])
            term = split_url[-2]
            response = tmdbsimple.Search().multi(query=term, page=page)

            for item in response["results"]:
                if item["media_type"] == "movie":
                    xml += get_movie_xml(item)
                elif item["media_type"] == "tv":
                    xml += get_show_xml(item)
                elif item["media_type"] == "person":
                    name = item["name"]
                    person_id = item["id"]
                    thumbnail = "https://image.tmdb.org/t/p/w1280/" + item["profile_path"]
                    xml += "<dir>\n"\
                           "\t<title>%s Shows TMDB</title>\n"\
                           "\t<tmdb>person/shows/%s</tmdb>\n"\
                           "\t<thumbnail>%s</thumbnail>\n"\
                           "</dir>\n\n" % (name.capitalize(),
                                           person_id,
                                           thumbnail)

                    xml += "<dir>\n"\
                           "\t<title>%s Movies TMDB</title>\n"\
                           "\t<tmdb>person/movies/%s</tmdb>\n"\
                           "\t<thumbnail>%s</thumbnail>\n"\
                           "\t</dir>\n\n" % (name.capitalize(),
                                             person_id,
                                             thumbnail)

        if page < response.get("total_pages", 0):
            base = url.split("/")
            if base[-1].isdigit():
                base = base[:-1]
            next_url = "/".join(base) + "/" + str(page + 1)
            xml += "<dir>"\
                   "<title>Next Page >></title>"\
                   "<tmdb>%s</tmdb>"\
                   "<summary>Go To Page %s</summary>"\
                   "</dir>" % (next_url, page + 1)
        save_to_db(xml, url)

    jenlist = JenList(xml)
    display_list(jenlist.get_list(), jenlist.get_content_type())


def get_movie_xml(item):
    title = remove_non_ascii(item["title"])
    year = item["release_date"].split("-")[0]
    tmdb_id = item["id"]
    url = "tmdb_imdb({0})".format(tmdb_id)
    imdb = fetch_from_db(url)
    if not imdb:
        imdb = item.get("imdb_id", "")
        if not imdb:
            imdb = tmdbsimple.Movies(tmdb_id).info()["imdb_id"]
        save_to_db(imdb, url)
    if item["poster_path"]:
        thumbnail = "https://image.tmdb.org/t/p/w1280/" + item["poster_path"]
    else:
        thumbnail = ""
    if item.get("backdrop_path", ""):
        fanart = "https://image.tmdb.org/t/p/w1280/" + item["backdrop_path"]
    else:
        fanart = ""
    xml = "<item>" \
          "<title>%s</title>" \
          "<meta>" \
          "<imdb>%s</imdb>"\
          "<content>movie</content>" \
          "<title>%s</title>" \
          "<year>%s</year>" \
          "</meta>" \
          "<link>" \
          "<sublink>search</sublink>" \
          "<sublink>searchsd</sublink>" \
          "</link>" \
          "<thumbnail>%s</thumbnail>" \
          "<fanart>%s</fanart>" \
          "</item>" % (title, imdb, title, year, thumbnail, fanart)
    return xml


def get_show_xml(item):
    title = remove_non_ascii(item["name"])
    year = item["first_air_date"].split("-")[0]
    tmdb_id = item["id"]
    if item["poster_path"]:
        thumbnail = "https://image.tmdb.org/t/p/w1280/" + item["poster_path"]
    else:
        thumbnail = ""
    if item.get("backdrop_path", ""):
        fanart = "https://image.tmdb.org/t/p/w1280/" + item["backdrop_path"]
    else:
        fanart = ""
    if tmdb_id:
        url = "tmdb_imdb({0})".format(tmdb_id)
        imdb = fetch_from_db(url)
        if not imdb:
            imdb = tmdbsimple.TV(tmdb_id).external_ids()['imdb_id']
            save_to_db(imdb, url)
    else:
        imdb = "0"

    xml = "<dir>"\
          "<title>%s</title>"\
          "<meta>"\
          "<imdb>%s</imdb>"\
          "<content>tvshow</content>"\
          "<tvshowtitle>%s</tvshowtitle>"\
          "<year>%s</year>"\
          "</meta>"\
          "<link>tmdb_tv_show(%s, %s, %s)</link>"\
          "<thumbnail>%s</thumbnail>" \
          "<fanart>%s</fanart>"\
          "</dir>" % (title, imdb, title, year, tmdb_id, year, title,
                      thumbnail, fanart)
    return xml


def get_season_xml(item, tmdb_id, year, tvtitle):
    season = item["season_number"]
    if item["poster_path"]:
        thumbnail = "https://image.tmdb.org/t/p/w1280/" + item["poster_path"]
    else:
        thumbnail = ""
    if item.get("backdrop_path", ""):
        fanart = "https://image.tmdb.org/t/p/w1280/" + item["backdrop_path"]
    else:
        fanart = ""
    if tmdb_id:
        url = "tmdb_imdb({0})".format(tmdb_id)
        imdb = fetch_from_db(url)
        if not imdb:
            imdb = tmdbsimple.TV(tmdb_id).external_ids()['imdb_id']
            save_to_db(imdb, url)
    else:
        imdb = "0"

    xml = "<dir>"\
          "<title>Season %s</title>"\
          "<meta>"\
          "<imdb>%s</imdb>"\
          "<content>season</content>"\
          "<season>%s</season>"\
          "</meta>"\
          "<thumbnail>%s</thumbnail>"\
          "<fanart>%s</fanart>"\
          "<link>tmdb_season(%s,%s, %s, %s)</link>"\
          "</dir>" % (season, imdb, season, thumbnail, fanart, tmdb_id,
                      season, year, tvtitle)
    return xml


def get_episode_xml(item, tmdb_id, year, tvtitle):
    title = remove_non_ascii(item["name"])
    season = item["season_number"]
    episode = item["episode_number"]
    if tmdb_id:
        url = "tmdb_imdb({0})".format(tmdb_id)
        imdb = fetch_from_db(url)
        if not imdb:
            imdb = tmdbsimple.TV(tmdb_id).external_ids()['imdb_id']
            save_to_db(imdb, url)
    else:
        imdb = "0"
    premiered = item["air_date"]
    if item["still_path"]:
        thumbnail = "https://image.tmdb.org/t/p/w1280/" + item["still_path"]
    else:
        thumbnail = ""
    if item.get("backdrop_path", ""):
        fanart = "https://image.tmdb.org/t/p/w1280/" + item["backdrop_path"]
    else:
        fanart = ""
    xml = "<item>"\
          "<title>%s</title>"\
          "<meta>"\
          "<imdb>%s</imdb>"\
          "<content>episode</content>"\
          "<tvshowtitle>%s</tvshowtitle>"\
          "<year>%s</year>"\
          "<title>%s</title>"\
          "<premiered>%s</premiered>"\
          "<season>%s</season>"\
          "<episode>%s</episode>"\
          "</meta>"\
          "<link>"\
          "<sublink>search</sublink>"\
          "<sublink>searchsd</sublink>"\
          "</link>"\
          "<thumbnail>%s</thumbnail>"\
          "<fanart>%s</fanart>"\
          "</item>" % (title, imdb, tvtitle, year, title,
                       premiered, season, episode, thumbnail, fanart)
    return xml


@route(mode='tmdb_tv_show', args=["url"])
def tmdb_tv_show(url):
    xml = fetch_from_db(url)
    if not xml:
        xml = ""
        splitted = url.replace("tmdb_id", "").split(",")
        tmdb_id = splitted[0]
        year = splitted[1]
        tvtitle = ",".join(splitted[2:])
        response = tmdbsimple.TV(tmdb_id).info()
        seasons = response["seasons"]
        xml = ""
        for season in seasons:
            xml += get_season_xml(season, tmdb_id, year, tvtitle)
        save_to_db(xml, url)
    jenlist = JenList(xml)
    display_list(jenlist.get_list(), jenlist.get_content_type())


@route(mode='tmdb_season', args=["url"])
def tmdb_season(url):
    xml = fetch_from_db(url)
    if not xml:
        xml = ""
        splitted = url.replace("tmdb_id", "").split(",")
        tmdb_id = splitted[0]
        season = splitted[1]
        year = splitted[2]
        tvtitle = ",".join(splitted[3:])
        response = tmdbsimple.TV_Seasons(tmdb_id, season).info()
        episodes = response["episodes"]
        xml = ""
        for episode in episodes:
            xml += get_episode_xml(episode, tmdb_id, year, tvtitle)
        save_to_db(xml, url)
    jenlist = JenList(xml)
    display_list(jenlist.get_list(), jenlist.get_content_type())


def remove_non_ascii(text):
    return unidecode(text)


def save_to_db(item, url):
    koding.reset_db()
    koding.Remove_From_Table(
        "tmdb_plugin",
        {
            "url": url
        })

    koding.Add_To_Table("tmdb_plugin",
                        {
                            "url": url,
                            "item": pickle.dumps(item).replace("\"", "'"),
                            "created": time.time()
                        })


def fetch_from_db(url):
    koding.reset_db()
    tmdb_plugin_spec = {
        "columns": {
            "url": "TEXT",
            "item": "TEXT",
            "created": "TEXT"
        },
        "constraints": {
            "unique": "url"
        }
    }
    koding.Create_Table("tmdb_plugin", tmdb_plugin_spec)
    match = koding.Get_From_Table(
        "tmdb_plugin", {"url": url})
    if match:
        match = match[0]
        if not match["item"]:
            return None
        created_time = match["created"]
        if created_time and float(created_time) <= time.time() + CACHE_TIME:
            match_item = match["item"].replace("'", "\"")
            try:
                match_item = match_item.encode('ascii', 'ignore')
            except:
                match_item = match_item.decode('utf-8').encode('ascii', 'ignore')
            return pickle.loads(match_item)
        else:
            return []
    else:
        return []
