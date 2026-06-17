from __future__ import annotations

from urllib.parse import urlparse
import re

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models import Article
from app.storage import utc_now


SEARCH_TERMS = [
    "인공지능 OR AI",
    "보안 개인정보",
    "클라우드 데이터센터",
    "반도체 스타트업",
    "빅테크 소프트웨어",
]


def is_korean_article(*parts: str) -> bool:
    text = " ".join(part or "" for part in parts)
    return len(re.findall(r"[가-힣]", text)) >= 8


def infer_category(text: str) -> str:
    pairs = [
        ("보안", "보안"),
        ("개인정보", "보안"),
        ("클라우드", "클라우드"),
        ("데이터센터", "데이터센터"),
        ("반도체", "반도체"),
        ("스타트업", "스타트업"),
        ("AI", "AI"),
        ("인공지능", "AI"),
        ("빅테크", "빅테크"),
    ]
    for needle, category in pairs:
        if needle.lower() in text.lower():
            return category
    return "IT"


def fetch_article_body(url: str) -> tuple[str, str]:
    try:
        with httpx.Client(timeout=8, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "ITBriefBot/0.1"})
            response.raise_for_status()
    except Exception:
        return "", "failed"

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    article = soup.find("article") or soup.body
    if not article:
        return "", "failed"
    paragraphs = [
        paragraph.get_text(" ", strip=True)
        for paragraph in article.find_all("p")
        if len(paragraph.get_text(strip=True)) > 40
    ]
    text = "\n".join(paragraphs)
    if not text:
        return "", "failed"
    return text[:6000], "completed"


def fetch_newsapi_articles(limit: int = 50) -> tuple[list[Article], str]:
    if not settings.news_api_key:
        return [], "NEWS_API_KEY가 없어 샘플 기사로 부트스트랩합니다."

    articles: list[Article] = []
    seen_urls: set[str] = set()
    per_term = 100

    with httpx.Client(timeout=12) as client:
        for term in SEARCH_TERMS:
            response = client.get(
                settings.news_api_endpoint,
                params={
                    "q": term,
                    "pageSize": min(100, per_term),
                    "sortBy": "publishedAt",
                    "apiKey": settings.news_api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "ok":
                raise RuntimeError(payload.get("message", "News API error"))
            for item in payload.get("articles", []):
                url = item.get("url") or ""
                title = item.get("title") or ""
                if not url or not title or url in seen_urls:
                    continue
                description = item.get("description") or ""
                if not is_korean_article(title, description):
                    continue
                seen_urls.add(url)
                body, extraction_status = fetch_article_body(url)
                source = item.get("source") or {}
                source_name = source.get("name") or urlparse(url).netloc or "Unknown"
                content = body or item.get("content") or description
                if not is_korean_article(title, description, content):
                    continue
                category = infer_category(f"{title} {description} {content}")
                articles.append(
                    Article(
                        id=None,
                        title=title,
                        url=url,
                        source_name=source_name,
                        source_url=f"{urlparse(url).scheme}://{urlparse(url).netloc}",
                        published_at=item.get("publishedAt") or utc_now(),
                        description=description,
                        content_text=content,
                        image_url=item.get("urlToImage") or "",
                        image_alt=title,
                        image_source=source_name,
                        author_name=item.get("author") or "",
                        category=category,
                        extraction_status=extraction_status,
                        display_weight=80 if item.get("urlToImage") else 50,
                    )
                )
                if len(articles) >= limit:
                    return articles, "News API 수집 완료"
    return articles, "News API 수집 완료"
