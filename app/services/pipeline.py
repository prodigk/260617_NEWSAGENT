from __future__ import annotations

from app.config import settings
from app.models import Article
from app.services.analyzer import analyze_article
from app.services.collector import fetch_newsapi_articles, is_korean_article
from app.services.seed import sample_articles
from app.services.vector_store import ArticleVectorIndex
from app.storage import (
    article_count,
    create_job,
    delete_articles,
    delete_seed_articles,
    get_recommendations,
    has_seed_articles,
    keep_latest_articles,
    list_articles,
    save_recommendations,
    update_article_analysis,
    update_job,
    upsert_articles,
)


def bootstrap_if_needed() -> None:
    _prune_non_korean_articles()
    count = article_count()
    should_try_newsapi = (
        settings.initial_fetch_on_startup
        and bool(settings.news_api_key)
        and (count < settings.news_fetch_limit or has_seed_articles())
    )
    if should_try_newsapi:
        if _bootstrap_from_newsapi():
            return
    if count == 0:
        _bootstrap_from_seed()
    keep_latest_articles(settings.news_fetch_limit)


def _prune_non_korean_articles() -> None:
    non_korean_ids = [
        article.id
        for article in list_articles()
        if article.id is not None
        and not is_korean_article(article.title, article.description, article.content_text)
    ]
    delete_articles(non_korean_ids)


def _bootstrap_from_seed() -> None:
    articles = sample_articles(settings.initial_news_count)
    inserted = upsert_articles(articles)
    job_id = create_job("completed", "첫 실행 샘플 데이터로 부트스트랩했습니다.")
    update_job(
        job_id,
        "completed",
        collected_count=len(articles),
        success_count=inserted or len(articles),
        failed_count=0,
        message="API 키 입력 전에도 화면을 확인할 수 있도록 샘플 데이터를 준비했습니다.",
        stages={
            "News API 수집": "sample",
            "중복 제거": "completed",
            "원문 본문 추출": "sample",
            "OpenAI/LangChain 분석": "fallback",
            "Chroma 저장": "fallback",
            "관련기사 추천": "fallback",
        },
    )


def _bootstrap_from_newsapi() -> bool:
    job_id = create_job("collecting", "첫 실행 News API 초기 데이터를 불러옵니다.")
    stages = {
        "News API 수집": "running",
        "중복 제거": "waiting",
        "원문 본문 추출": "waiting",
        "OpenAI/LangChain 분석": "waiting",
        "Chroma 저장": "waiting",
        "관련기사 추천": "waiting",
    }
    try:
        articles, message = fetch_newsapi_articles(limit=settings.initial_news_count)
        if not articles:
            raise RuntimeError("News API 초기 기사 결과가 비어 있습니다.")
        stages["News API 수집"] = "completed"
        stages["중복 제거"] = "completed"
        stages["원문 본문 추출"] = "completed"

        if has_seed_articles():
            delete_seed_articles()
        inserted = upsert_articles(articles)
        keep_latest_articles(settings.news_fetch_limit)
        stored = list_articles(sort="weight")

        stages["OpenAI/LangChain 분석"] = "fallback"
        analyzed: list[Article] = []
        for article in stored:
            updated = analyze_article(article, use_openai=False)
            update_article_analysis(updated)
            analyzed.append(updated)

        stages["Chroma 저장"] = "fallback"
        stages["관련기사 추천"] = "running"
        index = ArticleVectorIndex()
        refreshed = list_articles(sort="weight")
        for article in refreshed:
            if article.id is None:
                continue
            related = index.related(article, refreshed, limit=4)
            save_recommendations(article.id, related)
            article.related_count = len(related)
            update_article_analysis(article)
        stages["관련기사 추천"] = "completed"

        update_job(
            job_id,
            "completed",
            collected_count=len(articles),
            success_count=inserted or len(articles),
            failed_count=0,
            message=f"{message} 첫 화면용 초기 데이터를 준비했습니다.",
            stages=stages,
        )
        return True
    except Exception as exc:
        stages = {
            key: ("failed" if value == "running" else value)
            for key, value in stages.items()
        }
        update_job(
            job_id,
            "failed",
            failed_count=1,
            message=f"News API 초기 데이터 수집 실패: {exc}",
            stages=stages,
        )
        return False


def refresh_articles(use_seed_when_needed: bool = True) -> int:
    job_id = create_job("collecting", "최신기사 수집을 시작했습니다.")
    stages = {
        "News API 수집": "running",
        "중복 제거": "waiting",
        "원문 본문 추출": "waiting",
        "OpenAI/LangChain 분석": "waiting",
        "Chroma 저장": "waiting",
        "관련기사 추천": "waiting",
    }
    try:
        articles, message = fetch_newsapi_articles(limit=settings.news_fetch_limit)
        if not articles and use_seed_when_needed:
            articles = sample_articles(30)
            message = "API 키가 없어 샘플 데이터로 실행했습니다."
        stages["News API 수집"] = "completed"
        stages["중복 제거"] = "completed"
        stages["원문 본문 추출"] = "completed"
        inserted = upsert_articles(articles)
        keep_latest_articles(settings.news_fetch_limit)

        stored = list_articles(sort="weight")
        analyzed: list[Article] = []
        stages["OpenAI/LangChain 분석"] = "running"
        for article in stored:
            if article.analysis_status == "embedded" and article.summary_one_line:
                analyzed.append(article)
                continue
            updated = analyze_article(article)
            update_article_analysis(updated)
            analyzed.append(updated)
        stages["OpenAI/LangChain 분석"] = "completed"

        refreshed = list_articles(sort="weight")
        index = ArticleVectorIndex()
        stages["Chroma 저장"] = "running"
        index.upsert(refreshed)
        stages["Chroma 저장"] = "completed" if index.available() else "fallback"

        stages["관련기사 추천"] = "running"
        for article in refreshed:
            if article.id is None:
                continue
            related = index.related(article, refreshed, limit=4)
            save_recommendations(article.id, related)
            article.related_count = len(related)
            update_article_analysis(article)
        stages["관련기사 추천"] = "completed"

        update_job(
            job_id,
            "completed",
            collected_count=len(articles),
            success_count=len(refreshed),
            failed_count=0,
            message=message,
            stages=stages,
        )
        return inserted
    except Exception as exc:
        stages = {key: ("failed" if value == "running" else value) for key, value in stages.items()}
        update_job(
            job_id,
            "failed",
            failed_count=1,
            message=str(exc),
            stages=stages,
        )
        if article_count() == 0 and use_seed_when_needed:
            articles = sample_articles(30)
            upsert_articles(articles)
        return 0


def recommendations_for(article_id: int):
    return get_recommendations(article_id)
