from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Article:
    id: int | None
    title: str
    url: str
    source_name: str
    published_at: str
    description: str = ""
    content_text: str = ""
    image_url: str = ""
    image_alt: str = ""
    image_source: str = ""
    source_url: str = ""
    source_profile_image_url: str = ""
    source_description: str = ""
    author_name: str = ""
    author_profile_image_url: str = ""
    category: str = "IT"
    extraction_status: str = "pending"
    analysis_status: str = "pending"
    display_weight: int = 0
    summary_one_line: str = ""
    summary_three_lines: str = ""
    why_it_matters: str = ""
    follow_up_points: str = ""
    keywords: list[str] = field(default_factory=list)
    sentiment_label: str = "중립"
    sentiment_score: int = 50
    related_count: int = 0
    collected_at: str = ""
    duplicate_hash: str = ""


@dataclass
class RelatedArticle:
    article_id: int
    title: str
    reason: str
    score: float
    shared_keywords: list[str] = field(default_factory=list)


@dataclass
class CollectionJob:
    id: int | None
    status: str
    started_at: str
    finished_at: str = ""
    target_count: int = 100
    collected_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    message: str = ""
    stages: dict[str, str] = field(default_factory=dict)

