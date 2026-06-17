from __future__ import annotations

import json
import re
from collections import Counter

from app.config import settings
from app.models import Article


KEYWORD_HINTS = [
    "AI",
    "인공지능",
    "보안",
    "클라우드",
    "반도체",
    "스타트업",
    "빅테크",
    "데이터센터",
    "개인정보",
    "소프트웨어",
    "규제",
    "투자",
]


def _heuristic_keywords(text: str) -> list[str]:
    found = [word for word in KEYWORD_HINTS if word.lower() in text.lower()]
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
    common = [word for word, _ in Counter(tokens).most_common(8)]
    merged: list[str] = []
    for word in found + common:
        if word not in merged and len(merged) < 5:
            merged.append(word)
    return merged or ["IT", "기술", "시장 변화"]


def _heuristic_sentiment(text: str) -> tuple[str, int]:
    negative = ["위험", "실패", "침해", "규제", "감소", "비용", "논란", "유출"]
    positive = ["성장", "투자", "출시", "개선", "확대", "협력", "수익", "채택"]
    n = sum(1 for word in negative if word in text)
    p = sum(1 for word in positive if word in text)
    if p > n:
        return "긍정", min(90, 60 + p * 7)
    if n > p:
        return "부정", min(88, 60 + n * 7)
    return "중립", 55


def _fallback_analysis(article: Article) -> Article:
    text = f"{article.title}\n{article.description}\n{article.content_text}"
    keywords = _heuristic_keywords(text)
    sentiment, score = _heuristic_sentiment(text)
    article.keywords = keywords
    article.sentiment_label = sentiment
    article.sentiment_score = score
    article.summary_one_line = (
        article.description[:95]
        if article.description
        else f"{article.title} 이슈가 IT 시장의 다음 판단 지점으로 떠올랐습니다."
    )
    article.summary_three_lines = (
        f"{article.summary_one_line}\n"
        f"핵심 키워드는 {', '.join(keywords[:3])}입니다.\n"
        "관련 기업 발표와 규제 변화, 제품 업데이트를 함께 확인할 필요가 있습니다."
    )
    article.why_it_matters = (
        "사용자가 단순 기사 소비를 넘어 기술 도입, 비용, 리스크를 빠르게 판단할 수 있기 때문입니다."
    )
    article.follow_up_points = "후속 기사, 원문 발표, 관련 기업의 공식 업데이트를 확인하세요."
    article.analysis_status = "embedded"
    article.display_weight = (80 if article.image_url else 45) + score // 5
    return article


def analyze_article(article: Article, use_openai: bool = True) -> Article:
    if not use_openai or not settings.openai_api_key:
        return _fallback_analysis(article)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=settings.openai_model, temperature=0.2)
        text = f"{article.title}\n{article.description}\n{article.content_text[:3000]}"
        messages = [
            SystemMessage(
                content=(
                    "너는 한국어 IT 뉴스 분석 에디터다. 반드시 JSON만 반환한다. "
                    "필드: summary_one_line, summary_three_lines, why_it_matters, "
                    "follow_up_points, keywords(array), sentiment_label(긍정/중립/부정), sentiment_score(0-100)."
                )
            ),
            HumanMessage(content=text),
        ]
        response = llm.invoke(messages)
        payload = json.loads(str(response.content).strip())
        article.summary_one_line = payload.get("summary_one_line", "")
        article.summary_three_lines = payload.get("summary_three_lines", "")
        article.why_it_matters = payload.get("why_it_matters", "")
        article.follow_up_points = payload.get("follow_up_points", "")
        article.keywords = list(payload.get("keywords", []))[:5]
        article.sentiment_label = payload.get("sentiment_label", "중립")
        article.sentiment_score = int(payload.get("sentiment_score", 50))
        article.analysis_status = "sentimented"
        article.display_weight = (80 if article.image_url else 45) + article.sentiment_score // 5
        return article
    except Exception:
        article = _fallback_analysis(article)
        article.analysis_status = "failed"
        return article
