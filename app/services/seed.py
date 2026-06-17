from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import Article


TOPICS = [
    ("AI 에이전트", "AI", "긍정", 82),
    ("반도체 공급망", "반도체", "중립", 58),
    ("클라우드 비용", "클라우드", "부정", 71),
    ("개인정보 보안", "보안", "부정", 77),
    ("스타트업 투자", "스타트업", "중립", 54),
    ("데이터센터 전력", "데이터센터", "중립", 62),
    ("오픈소스 모델", "AI", "긍정", 76),
    ("빅테크 규제", "빅테크", "부정", 68),
    ("개발자 도구", "소프트웨어", "긍정", 80),
    ("모바일 온디바이스 AI", "AI", "긍정", 74),
]


IMAGES = [
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
]


def sample_articles(count: int = 30) -> list[Article]:
    now = datetime.now(timezone.utc)
    articles: list[Article] = []
    for index in range(count):
        topic, category, sentiment, score = TOPICS[index % len(TOPICS)]
        published = now - timedelta(hours=index * 2)
        title = f"{topic} 이슈가 한국 IT 시장에 남긴 {index + 1}번째 신호"
        description = (
            f"{topic} 관련 최신 변화가 기업 전략, 개발 조직, 인프라 투자 판단에 "
            "새로운 기준을 만들고 있습니다."
        )
        keywords = [topic, category, "한국 IT", "시장 변화"]
        articles.append(
            Article(
                id=None,
                title=title,
                url=f"https://example.com/it-brief/{index + 1}",
                source_name=["테크브리프", "AI데일리", "클라우드노트", "보안저널"][
                    index % 4
                ],
                source_url="https://example.com",
                source_profile_image_url="",
                author_name=["편집팀", "김민준", "이서연", "박지훈"][index % 4],
                published_at=published.isoformat(timespec="seconds"),
                description=description,
                content_text=(
                    description
                    + " 실무자는 단순 뉴스보다 영향 범위, 관련 기업, 다음 신호를 "
                    "함께 확인해야 합니다."
                ),
                image_url=IMAGES[index % len(IMAGES)] if index % 3 != 2 else "",
                image_alt=f"{topic} 기사 이미지",
                category=category,
                extraction_status="completed",
                analysis_status="embedded",
                display_weight=100 - index,
                summary_one_line=f"{topic} 변화가 국내 IT 의사결정의 우선순위를 바꾸고 있습니다.",
                summary_three_lines=(
                    f"{topic} 이슈는 기술 도입 속도와 비용 구조에 영향을 줍니다.\n"
                    "기업은 공급자 선택, 보안 검토, 운영 리스크를 함께 봐야 합니다.\n"
                    "다음 신호는 투자 발표, 규제 문서, 제품 업데이트입니다."
                ),
                why_it_matters=(
                    "단순 트렌드가 아니라 예산, 인력, 제품 로드맵에 연결되는 이슈입니다."
                ),
                follow_up_points="관련 기업 발표, 규제 변화, 경쟁 제품 업데이트를 확인하세요.",
                keywords=keywords,
                sentiment_label=sentiment,
                sentiment_score=score,
                related_count=3,
            )
        )
    return articles

