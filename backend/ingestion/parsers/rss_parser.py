import feedparser
from datetime import datetime

def parse_rss(feed_url: str, source_name: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    docs = []

    for entry in feed.entries:
        doc = {
            "doc_id": entry.get("id", entry.get("link", "")),
            "source_type": "news",
            "publisher": source_name,
            "source_url": entry.get("link", ""),
            "published_at": entry.get("published", datetime.utcnow().isoformat()),
            "title": entry.get("title", ""),
            "body": entry.get("summary", "") or entry.get("description", ""),

        } 

        if doc["title"] and doc["source_url"]:
            docs.append(doc)

    return docs


