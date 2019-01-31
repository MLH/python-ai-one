import requests
from bs4 import BeautifulSoup
import re
import os

CONTENT_CLASS_NAME = "mw-parser-output"
IGNORED_CONTENT_CLASS_NAMES = ["reflist", "thumb", "collapsible", "navbox", "infobox"]
CONTENT_CONTAINER_TAGS = ["p", "li", "td", "tr", "div"]
DATE_REGEX = re.compile(r"(?<!\d{1})(?:[1][0-9]{3}|[2][0][0-1][0-9])(?!\d{1})", re.M)


def has_class(el, class_name):
    el = el or {}
    classes = dict(el.attrs).get("class") or []

    return class_name in classes


def has_classes(el, class_names):
    class_names = class_names or []
    return any(class_name for class_name in class_names if has_class(el, class_name))


def get_article_body(url):
    # Gets the HTML content from your URL
    response = requests.get(url)
    html = response.content

    # We now use the BeautifulSoup library passing the second param so it will treat the case where we have HTML entities
    soup = BeautifulSoup(html, features="html.parser")
    
    # Now we make our first search selecting the main text content that we want to scan for dates
    return soup.find("div", attrs={"class": CONTENT_CLASS_NAME})


def get_event_container(block):
    content_container = None
    event_text = block.find(text=DATE_REGEX).parent

    for tag in CONTENT_CONTAINER_TAGS:
        if content_container:
            break

        container = event_text.find_parent(tag)
        if container and not has_class(container, CONTENT_CLASS_NAME):
            content_container = container

    return content_container or event_text


def create_timeline_from_wikipedia_content(element):
    timeline = {}

    for block in element.contents:
        # check if block is a navigable string
        if block.string == None:
            for match in re.finditer(DATE_REGEX, block.text):
                if match and not has_classes(block, IGNORED_CONTENT_CLASS_NAMES):
                    date = match.group(0)
                    content_container = get_event_container(block)
                    content = content_container.get_text()
                    events = timeline.get(date) or []

                    if len(content) >= 30 and not content in events:
                        timeline[date] = events + [content]
    return timeline


def create_timeline_from_wikipedia(url):
    return create_timeline_from_wikipedia_content(get_article_body(url))


# Sort the items by date and show the timeline
def sort_and_print_timeline(timeline):
    for date in sorted(timeline.iterkeys()):
        print "%s:" % (date)

        for event in timeline[date]:
            print "* %s" % (event.encode("utf8"))

        print "----"


url = os.environ.get('URL') or "https://en.wikipedia.org/wiki/Thor_(Marvel_Comics)"
timeline = create_timeline_from_wikipedia(url)
sort_and_print_timeline(timeline)