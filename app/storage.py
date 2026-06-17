from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterable

from app.config import settings
from app.models import Article, CollectionJob, RelatedArticle


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source_name TEXT NOT NULL,
                published_at TEXT NOT NULL,
                description TEXT DEFAULT '',
                content_text TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                image_alt TEXT DEFAULT '',
                image_source TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                source_profile_image_url TEXT DEFAULT '',
                source_description TEXT DEFAULT '',
                author_name TEXT DEFAULT '',
                author_profile_image_url TEXT DEFAULT '',
                category TEXT DEFAULT 'IT',
                extraction_status TEXT DEFAULT 'pending',
                analysis_status TEXT DEFAULT 'pending',
                display_weight INTEGER DEFAULT 0,
                summary_one_line TEXT DEFAULT '',
                summary_three_lines TEXT DEFAULT '',
                why_it_matters TEXT DEFAULT '',
                follow_up_points TEXT DEFAULT '',
                keywords TEXT DEFAULT '[]',
                sentiment_label TEXT DEFAULT '중립',
                sentiment_score INTEGER DEFAULT 50,
                related_count INTEGER DEFAULT 0,
                collected_at TEXT DEFAULT '',
                duplicate_hash TEXT DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT DEFAULT '',
                target_count INTEGER DEFAULT 100,
                collected_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                message TEXT DEFAULT '',
                stages TEXT DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                article_id INTEGER NOT NULL,
                related_article_id INTEGER NOT NULL,
                reason TEXT DEFAULT '',
                score REAL DEFAULT 0,
                shared_keywords TEXT DEFAULT '[]',
                UNIQUE(article_id, related_article_id)
            )
            """
        )


def article_hash(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode("utf-8")).hexdigest()


def row_to_article(row: sqlite3.Row) -> Article:
    return Article(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        source_name=row["source_name"],
        published_at=row["published_at"],
        description=row["description"] or "",
        content_text=row["content_text"] or "",
        image_url=row["image_url"] or "",
        image_alt=row["image_alt"] or "",
        image_source=row["image_source"] or "",
        source_url=row["source_url"] or "",
        source_profile_image_url=row["source_profile_image_url"] or "",
        source_description=row["source_description"] or "",
        author_name=row["author_name"] or "",
        author_profile_image_url=row["author_profile_image_url"] or "",
        category=row["category"] or "IT",
        extraction_status=row["extraction_status"] or "pending",
        analysis_status=row["analysis_status"] or "pending",
        display_weight=row["display_weight"] or 0,
        summary_one_line=row["summary_one_line"] or "",
        summary_three_lines=row["summary_three_lines"] or "",
        why_it_matters=row["why_it_matters"] or "",
        follow_up_points=row["follow_up_points"] or "",
        keywords=json.loads(row["keywords"] or "[]"),
        sentiment_label=row["sentiment_label"] or "중립",
        sentiment_score=row["sentiment_score"] or 50,
        related_count=row["related_count"] or 0,
        collected_at=row["collected_at"] or "",
        duplicate_hash=row["duplicate_hash"] or "",
    )


def upsert_articles(articles: Iterable[Article]) -> int:
    inserted = 0
    with connect() as conn:
        for article in articles:
            duplicate_hash = article.duplicate_hash or article_hash(
                article.url, article.title
            )
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO articles (
                    title, url, source_name, published_at, description, content_text,
                    image_url, image_alt, image_source, source_url,
                    source_profile_image_url, source_description, author_name,
                    author_profile_image_url, category, extraction_status,
                    analysis_status, display_weight, summary_one_line,
                    summary_three_lines, why_it_matters, follow_up_points,
                    keywords, sentiment_label, sentiment_score, related_count,
                    collected_at, duplicate_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.title,
                    article.url,
                    article.source_name,
                    article.published_at,
                    article.description,
                    article.content_text,
                    article.image_url,
                    article.image_alt,
                    article.image_source,
                    article.source_url,
                    article.source_profile_image_url,
                    article.source_description,
                    article.author_name,
                    article.author_profile_image_url,
                    article.category,
                    article.extraction_status,
                    article.analysis_status,
                    article.display_weight,
                    article.summary_one_line,
                    article.summary_three_lines,
                    article.why_it_matters,
                    article.follow_up_points,
                    json.dumps(article.keywords, ensure_ascii=False),
                    article.sentiment_label,
                    article.sentiment_score,
                    article.related_count,
                    article.collected_at or utc_now(),
                    duplicate_hash,
                ),
            )
            inserted += cursor.rowcount
    return inserted


def update_article_analysis(article: Article) -> None:
    if article.id is None:
        return
    with connect() as conn:
        conn.execute(
            """
            UPDATE articles
            SET content_text = ?, extraction_status = ?, analysis_status = ?,
                display_weight = ?, summary_one_line = ?, summary_three_lines = ?,
                why_it_matters = ?, follow_up_points = ?, keywords = ?,
                sentiment_label = ?, sentiment_score = ?, related_count = ?
            WHERE id = ?
            """,
            (
                article.content_text,
                article.extraction_status,
                article.analysis_status,
                article.display_weight,
                article.summary_one_line,
                article.summary_three_lines,
                article.why_it_matters,
                article.follow_up_points,
                json.dumps(article.keywords, ensure_ascii=False),
                article.sentiment_label,
                article.sentiment_score,
                article.related_count,
                article.id,
            ),
        )


def list_articles(
    query: str = "",
    category: str = "",
    sentiment: str = "",
    keyword: str = "",
    sort: str = "published",
) -> list[Article]:
    where = []
    params: list[str] = []
    if query:
        where.append("(title LIKE ? OR description LIKE ? OR content_text LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like, like])
    if category:
        where.append("category = ?")
        params.append(category)
    if sentiment:
        where.append("sentiment_label = ?")
        params.append(sentiment)
    if keyword:
        where.append("keywords LIKE ?")
        params.append(f"%{keyword}%")
    order_by = {
        "sentiment": "sentiment_score DESC, published_at DESC",
        "weight": "display_weight DESC, published_at DESC",
        "published": "published_at DESC",
    }.get(sort, "published_at DESC")
    sql = "SELECT * FROM articles"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {order_by}"
    with connect() as conn:
        return [row_to_article(row) for row in conn.execute(sql, params)]


def get_article(article_id: int) -> Article | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        return row_to_article(row) if row else None


def article_count() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM articles").fetchone()
        return int(row["count"])


def has_seed_articles() -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM articles WHERE url LIKE 'https://example.com/it-brief/%'"
        ).fetchone()
        return int(row["count"]) > 0


def delete_seed_articles() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM recommendations")
        conn.execute("DELETE FROM articles WHERE url LIKE 'https://example.com/it-brief/%'")


def delete_articles(article_ids: list[int]) -> None:
    if not article_ids:
        return
    placeholders = ",".join("?" for _ in article_ids)
    with connect() as conn:
        conn.execute(
            f"DELETE FROM recommendations WHERE article_id IN ({placeholders})",
            article_ids,
        )
        conn.execute(
            f"DELETE FROM recommendations WHERE related_article_id IN ({placeholders})",
            article_ids,
        )
        conn.execute(f"DELETE FROM articles WHERE id IN ({placeholders})", article_ids)


def keep_latest_articles(limit: int) -> None:
    with connect() as conn:
        conn.execute(
            """
            DELETE FROM recommendations
            WHERE article_id NOT IN (
                SELECT id FROM articles ORDER BY published_at DESC, id DESC LIMIT ?
            )
            OR related_article_id NOT IN (
                SELECT id FROM articles ORDER BY published_at DESC, id DESC LIMIT ?
            )
            """,
            (limit, limit),
        )
        conn.execute(
            """
            DELETE FROM articles
            WHERE id NOT IN (
                SELECT id FROM articles ORDER BY published_at DESC, id DESC LIMIT ?
            )
            """,
            (limit,),
        )


def create_job(status: str, message: str = "") -> int:
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO jobs (status, started_at, message, stages)
            VALUES (?, ?, ?, ?)
            """,
            (status, utc_now(), message, json.dumps({}, ensure_ascii=False)),
        )
        return int(cursor.lastrowid)


def update_job(
    job_id: int,
    status: str,
    *,
    collected_count: int = 0,
    success_count: int = 0,
    failed_count: int = 0,
    message: str = "",
    stages: dict[str, str] | None = None,
) -> None:
    finished_at = utc_now() if status in {"completed", "partial_failed", "failed"} else ""
    with connect() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = ?, finished_at = ?, collected_count = ?, success_count = ?,
                failed_count = ?, message = ?, stages = ?
            WHERE id = ?
            """,
            (
                status,
                finished_at,
                collected_count,
                success_count,
                failed_count,
                message,
                json.dumps(stages or {}, ensure_ascii=False),
                job_id,
            ),
        )


def latest_job() -> CollectionJob | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        return CollectionJob(
            id=row["id"],
            status=row["status"],
            started_at=row["started_at"],
            finished_at=row["finished_at"] or "",
            target_count=row["target_count"],
            collected_count=row["collected_count"],
            success_count=row["success_count"],
            failed_count=row["failed_count"],
            message=row["message"] or "",
            stages=json.loads(row["stages"] or "{}"),
        )


def save_recommendations(article_id: int, related: list[RelatedArticle]) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM recommendations WHERE article_id = ?", (article_id,))
        for item in related:
            conn.execute(
                """
                INSERT OR REPLACE INTO recommendations (
                    article_id, related_article_id, reason, score, shared_keywords
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    article_id,
                    item.article_id,
                    item.reason,
                    item.score,
                    json.dumps(item.shared_keywords, ensure_ascii=False),
                ),
            )


def get_recommendations(article_id: int) -> list[RelatedArticle]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT r.related_article_id, r.reason, r.score, r.shared_keywords, a.title
            FROM recommendations r
            JOIN articles a ON a.id = r.related_article_id
            WHERE r.article_id = ?
            ORDER BY r.score DESC
            """,
            (article_id,),
        ).fetchall()
        return [
            RelatedArticle(
                article_id=row["related_article_id"],
                title=row["title"],
                reason=row["reason"] or "",
                score=row["score"] or 0,
                shared_keywords=json.loads(row["shared_keywords"] or "[]"),
            )
            for row in rows
        ]
