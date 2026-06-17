from __future__ import annotations

from collections import Counter
from math import ceil

from app.config import settings
from app.models import Article


SLOT_PATTERN = [
    "hero",
    "feature",
    "feature",
    "brief",
    "brief",
    "feature",
    "brief",
    "related",
    "brief",
]


def paginate_articles(articles: list[Article], page: int, per_page: int | None = None) -> tuple[list[Article], int, int]:
    per_page = per_page or settings.articles_per_page
    total_pages = max(1, ceil(len(articles) / per_page))
    safe_page = min(max(page, 1), total_pages)
    start = (safe_page - 1) * per_page
    return articles[start : start + per_page], safe_page, total_pages


def build_slots(articles: list[Article]) -> list[dict]:
    sorted_articles = sorted(
        articles, key=lambda item: (item.display_weight, bool(item.image_url)), reverse=True
    )
    slots: list[dict] = []
    article_index = 0
    for slot_type in SLOT_PATTERN:
        if slot_type == "related":
            slots.append({"type": slot_type, "article": None})
            continue
        if article_index >= len(sorted_articles):
            break
        article = sorted_articles[article_index]
        if slot_type == "hero":
            image_articles = [item for item in sorted_articles if item.image_url]
            if image_articles:
                article = image_articles[0]
                sorted_articles.remove(article)
                article_index = 0
            else:
                article_index += 1
        else:
            article_index += 1
        slots.append({"type": slot_type, "article": article})
    return [slot for slot in slots if slot["type"] == "related" or slot["article"]]


def page_keywords(articles: list[Article]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for article in articles:
        counter.update(article.keywords)
    return counter.most_common(8)


def sentiment_summary(articles: list[Article]) -> dict[str, int]:
    counter = Counter(article.sentiment_label for article in articles)
    return {label: counter.get(label, 0) for label in ["긍정", "중립", "부정"]}


def all_keywords(articles: list[Article], limit: int = 20) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for article in articles:
        counter.update(article.keywords)
    return counter.most_common(limit)
