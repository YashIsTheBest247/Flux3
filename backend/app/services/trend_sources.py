"""
Where trends come from.

The pipeline used to read five Economic Times RSS feeds, which is a fine source
of Indian financial news and useless to a gaming channel. This module turns the
source into a per-profile choice: Google Trends for what a whole country is
searching, Reddit for what a community is actually arguing about, Hacker News
for tech, YouTube's own most-popular chart for what is winning on the platform
you are about to publish to, and plain RSS for everything else.

Every source is normalised into the same `Article` the existing ranker already
scores, so recency and cross-source keyword overlap work unchanged - and get
better, because a story that shows up on Google Trends *and* Reddit *and* a news
feed now has overlap evidence from three independent places instead of three
sections of one newspaper.

Playing fair
------------
Every source here is a public, free, documented endpoint. Requests go out with a
real User-Agent (Reddit rejects the default and is entitled to), each source is
capped, failures never take down a run, and results are cached for a few minutes
so a creator hammering Refresh in the dashboard does not hammer anyone's API.
"""
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote_plus

import feedparser
import requests

from app.core.config import settings
from app.services.trends_service import Article, _clean_html

logger = logging.getLogger(__name__)

# Reddit blocks the default python-requests agent outright, and their API rules
# ask for something identifying. Everyone else is happy with it too.
USER_AGENT = "Flux/1.0 (creator automation; +https://github.com/flux-creator)"
_HEADERS = {"User-Agent": USER_AGENT}

_TIMEOUT = 20
_MAX_WORKERS = 5

# Short-lived response cache. The dashboard polls, and a creator comparing
# profiles will hit these endpoints repeatedly within a minute or two; without
# this that becomes real traffic to somebody else's free API.
_CACHE_TTL_SECONDS = 300
_cache: Dict[str, Any] = {}


def _cached(key: str, producer: Callable[[], List[Article]]) -> List[Article]:
    hit = _cache.get(key)
    if hit and (time.time() - hit["at"]) < _CACHE_TTL_SECONDS:
        return list(hit["items"])
    items = producer()
    _cache[key] = {"at": time.time(), "items": list(items)}
    return items


def clear_cache() -> None:
    _cache.clear()


# ---------------------------------------------------------------- RSS --------

def fetch_rss(urls: List[str], limit: int = 40) -> List[Article]:
    """Any RSS or Atom feed. The original Economic Times path, generalised."""
    articles: List[Article] = []
    for url in urls:
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("RSS parse failed for %s: %s", url, exc)
            continue
        source = _clean_html(getattr(parsed.feed, "title", "")) or url
        for entry in parsed.entries[:limit]:
            link = (entry.get("link") or "").strip()
            title = _clean_html(entry.get("title", ""))
            if not link or not title:
                continue
            articles.append(Article(
                title=title,
                link=link,
                summary=_clean_html(entry.get("summary", ""))[:600],
                source=source,
                published_ts=_entry_ts(entry),
            ))
    return articles


def _entry_ts(entry) -> Optional[float]:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return time.mktime(parsed)
            except (OverflowError, ValueError):
                continue
    return None


# ------------------------------------------------------- Google Trends -------

def fetch_google_trends(geo: str = "US", limit: int = 25) -> List[Article]:
    """The daily trending-searches RSS feed - what a country is searching for.

    A published RSS endpoint, not a scrape. Each item carries the search term,
    an approximate traffic figure and the news article that drove it, which is
    exactly the raw material for a "what is everyone talking about today" video.
    """
    url = f"https://trends.google.com/trending/rss?geo={quote_plus(geo)}"
    try:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google Trends fetch failed (geo=%s): %s", geo, exc)
        return []

    articles: List[Article] = []
    for entry in parsed.entries[:limit]:
        title = _clean_html(entry.get("title", ""))
        if not title:
            continue
        traffic = entry.get("ht_approx_traffic") or ""
        # The feed nests the news story that caused the spike. It is a far
        # better script prompt than the bare search term, which is often two
        # words with no context at all.
        news_title = ""
        news_link = ""
        news_items = entry.get("ht_news_item") or []
        if isinstance(news_items, list) and news_items:
            first = news_items[0]
            news_title = _clean_html(first.get("ht_news_item_title", ""))
            news_link = (first.get("ht_news_item_url") or "").strip()
        elif isinstance(news_items, dict):
            news_title = _clean_html(news_items.get("ht_news_item_title", ""))
            news_link = (news_items.get("ht_news_item_url") or "").strip()

        summary = news_title or _clean_html(entry.get("description", ""))
        if traffic:
            summary = f"{summary} ({traffic} searches)".strip()

        articles.append(Article(
            title=title,
            # Falling back to a Trends permalink keeps `link` unique, which is
            # what the already-processed set is keyed on.
            link=news_link or f"https://trends.google.com/trends/explore?q={quote_plus(title)}&geo={geo}",
            summary=summary[:600],
            source=f"Google Trends {geo}",
            published_ts=_entry_ts(entry) or time.time(),
        ))
    return articles


# -------------------------------------------------------------- Reddit -------

def fetch_reddit(subreddits: List[str], limit: int = 15,
                 listing: str = "hot") -> List[Article]:
    """Public subreddit JSON - no key, no OAuth, 60 requests a minute.

    Reddit is the best signal in here for anything community-shaped: gaming,
    fitness, personal finance. Self-posts carry their body text, which makes a
    far richer script prompt than a headline alone.
    """
    articles: List[Article] = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{quote_plus(sub)}/{listing}.json"
        try:
            response = requests.get(
                url, headers=_HEADERS, params={"limit": limit, "raw_json": 1},
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            children = response.json().get("data", {}).get("children", [])
        except Exception as exc:  # noqa: BLE001
            # Reddit refuses the JSON API from some networks and hosts outright
            # - the connection is reset rather than refused, so there is no
            # status code to branch on. The RSS view of the same listing is
            # served differently and frequently survives; it carries no score
            # or comment count, which is a fair trade for having any data.
            logger.info("Reddit JSON failed for r/%s (%s); trying RSS.", sub, exc)
            fallback = fetch_rss([f"https://www.reddit.com/r/{quote_plus(sub)}/{listing}.rss"],
                                 limit=limit)
            for article in fallback:
                article.source = f"r/{sub}"
            if fallback:
                articles.extend(fallback)
            else:
                logger.warning("Reddit unavailable for r/%s via JSON and RSS.", sub)
            continue

        for child in children:
            post = child.get("data", {})
            title = _clean_html(post.get("title", ""))
            if not title or post.get("stickied") or post.get("over_18"):
                continue
            body = _clean_html(post.get("selftext", ""))[:600]
            articles.append(Article(
                title=title,
                link=f"https://www.reddit.com{post.get('permalink', '')}",
                summary=body or f"{post.get('score', 0)} upvotes, "
                                f"{post.get('num_comments', 0)} comments in r/{sub}",
                source=f"r/{sub}",
                published_ts=post.get("created_utc"),
            ))
    return articles


# --------------------------------------------------------- Hacker News -------

def fetch_hackernews(limit: int = 25, query: str = "") -> List[Article]:
    """HN via the Algolia API - public, free, no key, generous limits."""
    if query:
        url = f"https://hn.algolia.com/api/v1/search?query={quote_plus(query)}&tags=story"
    else:
        url = "https://hn.algolia.com/api/v1/search?tags=front_page"
    try:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()
        hits = response.json().get("hits", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Hacker News fetch failed: %s", exc)
        return []

    articles: List[Article] = []
    for hit in hits[:limit]:
        title = _clean_html(hit.get("title") or hit.get("story_title") or "")
        if not title:
            continue
        articles.append(Article(
            title=title,
            link=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            summary=f"{hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments on Hacker News",
            source="Hacker News",
            published_ts=hit.get("created_at_i"),
        ))
    return articles


# ---------------------------------------------------- YouTube trending -------

# YouTube's own category ids, for the chart call.
YOUTUBE_CATEGORIES = {
    "film": "1", "music": "10", "sports": "17", "gaming": "20",
    "entertainment": "24", "news": "25", "howto": "26", "education": "27",
    "science": "28",
}


def fetch_youtube_trending(region: str = "US", category: str = "",
                           limit: int = 25) -> List[Article]:
    """The most-popular chart for a region.

    The most directly useful source of the five: it is what is winning *on the
    platform you are about to publish to*, in the category you publish in.
    Needs the creator's connected channel, so it silently contributes nothing
    until they connect one - which is the right behaviour for a source that is
    a bonus rather than a requirement.
    """
    try:
        from app.services import youtube_service
        client = youtube_service._build_client()  # noqa: SLF001 - same package
    except Exception as exc:  # noqa: BLE001
        logger.info("YouTube trending skipped (no connected channel): %s", exc)
        return []

    params: Dict[str, Any] = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": min(limit, 50),
    }
    category_id = YOUTUBE_CATEGORIES.get(category.lower(), "") if category else ""
    if category_id:
        params["videoCategoryId"] = category_id

    try:
        response = client.videos().list(**params).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("YouTube trending fetch failed: %s", exc)
        return []

    articles: List[Article] = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        title = _clean_html(snippet.get("title", ""))
        if not title:
            continue
        published = snippet.get("publishedAt")
        ts = None
        if published:
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
            except Exception:  # noqa: BLE001
                ts = None
        articles.append(Article(
            title=title,
            link=f"https://www.youtube.com/watch?v={item.get('id')}",
            summary=(_clean_html(snippet.get("description", ""))[:400]
                     or f"{stats.get('viewCount', 0)} views"),
            source=f"YouTube trending ({snippet.get('channelTitle', region)})",
            published_ts=ts,
        ))
    return articles


# ---------------------------------------------------------- aggregation ------

_FETCHERS: Dict[str, Callable[..., List[Article]]] = {
    "rss": lambda cfg: fetch_rss(cfg.get("urls", []), cfg.get("limit", 40)),
    "google_trends": lambda cfg: fetch_google_trends(cfg.get("geo", "US"), cfg.get("limit", 25)),
    "reddit": lambda cfg: fetch_reddit(cfg.get("subreddits", []), cfg.get("limit", 15),
                                       cfg.get("listing", "hot")),
    "hackernews": lambda cfg: fetch_hackernews(cfg.get("limit", 25), cfg.get("query", "")),
    "youtube_trending": lambda cfg: fetch_youtube_trending(
        cfg.get("region", "US"), cfg.get("category", ""), cfg.get("limit", 25)),
}

AVAILABLE_SOURCES = sorted(_FETCHERS)


def fetch_all(sources: List[Dict[str, Any]]) -> List[Article]:
    """Fetch every configured source concurrently and merge the results.

    Concurrent because these are five independent network round trips and doing
    them in series makes the dashboard's Refresh feel broken. One source failing
    never takes down the others - a run with four of five sources is still a
    good run, and an empty list is not an error worth propagating.
    """
    if not sources:
        return []

    collected: List[Article] = []
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {}
        for spec in sources:
            kind = (spec.get("type") or "").strip().lower()
            fetcher = _FETCHERS.get(kind)
            if not fetcher:
                logger.warning("Unknown trend source type: %r", kind)
                continue
            cache_key = f"{kind}:{json.dumps(spec, sort_keys=True)}"
            futures[pool.submit(_cached, cache_key, lambda s=spec, f=fetcher: f(s))] = kind

        for future in as_completed(futures):
            kind = futures[future]
            try:
                items = future.result()
                logger.info("Trend source %s returned %d item(s).", kind, len(items))
                collected.extend(items)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Trend source %s failed: %s", kind, exc)

    return _dedupe(collected)


_NORMALISE_RE = re.compile(r"[^a-z0-9 ]+")


def _dedupe(articles: List[Article]) -> List[Article]:
    """Drop duplicates by link, then by normalised title.

    The title pass is the one that matters. The whole point of reading five
    sources is that a real story appears in several of them, and the same story
    under five different URLs would otherwise occupy all five top slots and
    produce five near-identical videos.
    """
    seen_links = set()
    seen_titles = set()
    unique: List[Article] = []
    for article in articles:
        link = (article.link or "").strip()
        title_key = _NORMALISE_RE.sub("", (article.title or "").lower()).strip()
        if link and link in seen_links:
            continue
        if title_key and title_key in seen_titles:
            continue
        if link:
            seen_links.add(link)
        if title_key:
            seen_titles.add(title_key)
        unique.append(article)
    return unique
