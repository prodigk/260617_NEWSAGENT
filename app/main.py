from __future__ import annotations

from collections import Counter
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.editorial import (
    all_keywords,
    build_slots,
    page_keywords,
    paginate_articles,
    sentiment_summary,
)
from app.services.pipeline import bootstrap_if_needed, recommendations_for, refresh_articles
from app.services.vector_store import ArticleVectorIndex
from app.storage import get_article, latest_job, list_articles, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    bootstrap_if_needed()
    yield


app = FastAPI(title="IT Brief", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def template_context(request: Request, **extra):
    articles = list_articles(sort="weight")
    job = latest_job()
    context = {
        "request": request,
        "latest_job": job,
        "total_articles": len(articles),
        "global_keywords": all_keywords(articles, limit=12),
        "global_sentiment": sentiment_summary(articles),
        "settings": settings,
    }
    context.update(extra)
    return context


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return news(request, page=1, q="", category="", sentiment="", keyword="", sort="published")


@app.get("/news", response_class=HTMLResponse)
def news(
    request: Request,
    page: int = Query(1, ge=1),
    q: str = "",
    category: str = "",
    sentiment: str = "",
    keyword: str = "",
    sort: str = "published",
):
    articles = list_articles(q, category, sentiment, keyword, sort)
    page_articles, current_page, total_pages = paginate_articles(articles, page)
    params = {
        "q": q,
        "category": category,
        "sentiment": sentiment,
        "keyword": keyword,
        "sort": sort,
    }
    base_query = urlencode({key: value for key, value in params.items() if value})
    return templates.TemplateResponse(
        "news.html",
        template_context(
            request,
            articles=articles,
            page_articles=page_articles,
            slots=build_slots(page_articles),
            page_keywords=page_keywords(page_articles),
            page_sentiment=sentiment_summary(page_articles),
            current_page=current_page,
            total_pages=total_pages,
            filters=params,
            base_query=base_query,
        ),
    )


@app.post("/refresh")
def refresh():
    refresh_articles(use_seed_when_needed=True)
    return RedirectResponse("/", status_code=303)


@app.get("/article/{article_id}", response_class=HTMLResponse)
def article_detail(request: Request, article_id: int):
    article = get_article(article_id)
    if not article:
        return RedirectResponse("/news", status_code=303)
    related = recommendations_for(article_id)
    return templates.TemplateResponse(
        "article.html",
        template_context(request, article=article, related=related),
    )


@app.get("/keywords", response_class=HTMLResponse)
def keywords(request: Request, keyword: str = ""):
    articles = list_articles(keyword=keyword) if keyword else list_articles(sort="weight")
    return templates.TemplateResponse(
        "keywords.html",
        template_context(
            request,
            selected_keyword=keyword,
            articles=articles,
            keywords=all_keywords(list_articles(sort="weight"), limit=30),
            sentiment=sentiment_summary(articles),
        ),
    )


@app.get("/sentiment", response_class=HTMLResponse)
def sentiment(request: Request):
    articles = list_articles(sort="sentiment")
    categories = Counter(article.category for article in articles)
    return templates.TemplateResponse(
        "sentiment.html",
        template_context(
            request,
            articles=articles,
            categories=categories.most_common(),
            sentiment=sentiment_summary(articles),
        ),
    )


@app.get("/search", response_class=HTMLResponse)
def semantic_search(request: Request, q: str = ""):
    articles = list_articles(sort="weight")
    results = []
    if q:
        results = ArticleVectorIndex().search(q, articles, limit=10)
    return templates.TemplateResponse(
        "search.html",
        template_context(request, query=q, results=results),
    )


@app.get("/status", response_class=HTMLResponse)
def status(request: Request):
    return templates.TemplateResponse(
        "status.html",
        template_context(request, articles=list_articles(sort="weight")),
    )
