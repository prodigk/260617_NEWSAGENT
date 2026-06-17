from app.models import Article
from app.services.editorial import build_slots, paginate_articles


def article(index: int, image: bool = True) -> Article:
    return Article(
        id=index,
        title=f"기사 {index}",
        url=f"https://example.com/{index}",
        source_name="테스트",
        published_at="2026-06-17T00:00:00Z",
        image_url="https://example.com/image.jpg" if image else "",
        display_weight=100 - index,
    )


def test_paginate_articles_keeps_last_page_natural():
    articles = [article(index) for index in range(23)]
    page_articles, current_page, total_pages = paginate_articles(articles, 3, per_page=10)
    assert current_page == 3
    assert total_pages == 3
    assert len(page_articles) == 3


def test_build_slots_includes_related_without_page_flow_section():
    articles = [article(index, image=index % 2 == 0) for index in range(8)]
    slots = build_slots(articles)
    slot_types = [slot["type"] for slot in slots]
    assert "hero" in slot_types
    assert "analysis" not in slot_types
    assert "related" in slot_types
