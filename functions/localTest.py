import typing

import pytz
import requests
import feedparser
import json
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

from typing import Set

category_map = {
    "34": "Advising",
    "33": "Careers",
    "67": "Grad",
    "27": "Health &amp; Wellness",
    "32": "New to UBC",
    "28": "UBCO Life",
    "1": "Uncategorized"
}


def parse_categories(response_input):
    categories = set()
    category_list = response_input['categories']
    for category in category_list:
        categories.add(category['name'])
    return categories


def get_all_categories(url):
    categories = set()
    json_response = requests.get(url).json()
    categories = categories.union(parse_categories(json_response))
    while json_response.get('next_rest_url') is not None:
        next_page = json_response['next_rest_url']
        json_response = requests.get(next_page).json()
        categories = categories.union(parse_categories(json_response))
    return categories


def get_all_blogs(url):
    blogs = []
    json_response = requests.get(url).json()
    for blog_item in json_response:
        blogs.append(blog_parser(blog_item))
    return blogs


def news_parser(news_json):
    parsed_news = {
        "id": news_json["post-id"],
        "title": news_json["title"],
        "link": news_json["id"],
        "categories": [category["term"] for category in news_json["tags"]],
        "summary": news_json["summary"],
        "media_thumbnail": news_json["media_thumbnail"]
    }
    return parsed_news


def get_blog_thumbnail(media_url):
    media_response = requests.get(media_url).json()
    image_links = {
        "full_image": media_response["guid"]["rendered"],
        "medium_image": media_response["media_details"]["sizes"]["medium"]["source_url"]
    }
    return image_links


def blog_parser(blog_json):
    try:
        image_links = get_blog_thumbnail(blog_json["_links"]["wp:featuredmedia"][0]["href"])
    except KeyError as e:
        print(e)
        image_links = "None"
    parsed_blog = {
        "id": blog_json["id"],
        "title": blog_json["title"]["rendered"],
        "date": blog_json["date"],
        "link": blog_json["guid"]["rendered"],
        "categories": [category_map[str(category)] for category in blog_json["categories"]],
        "excerpt": blog_json["excerpt"]["rendered"],
        "media_images": image_links
    }

    return parsed_blog


CATEGORY_MAP = {
    "34": "Advising",
    "33": "Careers",
    "67": "Grad",
    "27": "Health and Wellness",
    "32": "New to UBC",
    "28": "UBCO Life",
    "1": "Uncategorized"
}


def get_blog_thumbnail(media_url):
    """
    Performs a second REST API call to fetch the cover image urls for a blog post

    :param media_url: Media REST API url for blog images
    :return: Dictionary containing image links to two blog cover image sizes, 'fullImage' and 'mediumImage'
    """
    media_response = requests.get(media_url).json()
    image_links = {
        "fullImage": media_response["guid"]["rendered"],
        "mediumImage": media_response["media_details"]["sizes"]["medium"]["source_url"]
    }
    return image_links


def blog_parser(blog_json):
    """
    Parses blog items from the unaltered API response

    :param blog_json: Unaltered JSON item from UBCO news API Response
    :return: JSON formatted dictionary item for DynamoDB storage
    """
    try:
        image_links = get_blog_thumbnail(blog_json["_links"]["wp:featuredmedia"][0]["href"])
    except KeyError as e:
        # LOGGER.debug(json.dumps(e, indent=4))
        image_links = "None"
        parsed_blog = {
            "blogId": str(blog_json["id"]),
            "title": blog_json["title"]["rendered"],
            "dateModified": str(datetime.strptime(blog_json["date"], "%Y-%m-%dT%H:%M:%S")),
            "link": blog_json["guid"]["rendered"],
            "categories": [CATEGORY_MAP[str(category)] for category in blog_json["categories"]],
            "excerpt": blog_json["excerpt"]["rendered"],
            "mediaImages": image_links
        }
    return parsed_blog


def get_all_blogs(url):
    """
    Calls the blogs REST API, parses the resulting response and returns a list of parsed blog_items to be stored in
    DynamoDB

    :param url: Url for the REST API for UBCO Student Life Blogs
    :return: Parsed blog items in a JSON formatted list
    """
    blogs = []
    json_response = requests.get(url).json()
    for blog_item in json_response:
        blogs.append(blog_parser(blog_item))
    return blogs


with open("../parsed_data/newResult.json", "w") as file:
    blogs = get_all_blogs("https://students.ok.ubc.ca/wp-json/wp/v2/posts?order=asc")
    file.write(json.dumps(blogs, indent=4))
    # file.write(str(requests.get("https://events.ok.ubc.ca/wp-json/tribe/events/v1/events").json()))



