from __future__ import annotations

import math
from collections import Counter

from app.config import settings
from app.models import Article, RelatedArticle


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in text.replace("\n", " ").split() if len(token) > 1]


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    keys = set(left) | set(right)
    dot = sum(left[key] * right[key] for key in keys)
    l_norm = math.sqrt(sum(value * value for value in left.values()))
    r_norm = math.sqrt(sum(value * value for value in right.values()))
    if not l_norm or not r_norm:
        return 0.0
    return dot / (l_norm * r_norm)


class ArticleVectorIndex:
    def __init__(self) -> None:
        self._collection = None
        self._embeddings = None
        if settings.openai_api_key:
            try:
                from langchain_chroma import Chroma
                from langchain_openai import OpenAIEmbeddings

                self._embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model)
                self._collection = Chroma(
                    collection_name="it_brief_articles",
                    persist_directory=settings.chroma_path,
                    embedding_function=self._embeddings,
                )
            except Exception:
                self._collection = None
                self._embeddings = None

    def available(self) -> bool:
        return self._collection is not None

    def upsert(self, articles: list[Article]) -> None:
        if not self._collection:
            return
        docs = []
        metadatas = []
        ids = []
        for article in articles:
            if article.id is None:
                continue
            docs.append(self.document_text(article))
            metadatas.append(
                {
                    "article_id": article.id,
                    "title": article.title,
                    "source": article.source_name,
                    "category": article.category,
                }
            )
            ids.append(str(article.id))
        if docs:
            try:
                self._collection.add_texts(texts=docs, metadatas=metadatas, ids=ids)
            except Exception:
                # Chroma can reject existing ids on repeated refreshes; the app can
                # still serve keyword-based recommendations through the fallback path.
                return

    def related(self, article: Article, candidates: list[Article], limit: int = 4) -> list[RelatedArticle]:
        if article.id is None:
            return []
        if self._collection:
            try:
                results = self._collection.similarity_search_with_score(
                    self.document_text(article), k=limit + 1
                )
                related: list[RelatedArticle] = []
                by_id = {item.id: item for item in candidates}
                for doc, score in results:
                    article_id = int(doc.metadata.get("article_id", 0))
                    if article_id == article.id or article_id not in by_id:
                        continue
                    target = by_id[article_id]
                    shared = sorted(set(article.keywords) & set(target.keywords))
                    related.append(
                        RelatedArticle(
                            article_id=article_id,
                            title=target.title,
                            reason=self.reason(shared, target),
                            score=float(score),
                            shared_keywords=shared,
                        )
                    )
                if related:
                    return related[:limit]
            except Exception:
                pass
        return self._fallback_related(article, candidates, limit)

    def search(self, query: str, candidates: list[Article], limit: int = 8) -> list[tuple[Article, float]]:
        if self._collection:
            try:
                results = self._collection.similarity_search_with_score(query, k=limit)
                by_id = {item.id: item for item in candidates}
                matches: list[tuple[Article, float]] = []
                for doc, score in results:
                    article_id = int(doc.metadata.get("article_id", 0))
                    if article_id in by_id:
                        matches.append((by_id[article_id], float(score)))
                if matches:
                    return matches
            except Exception:
                pass
        query_vector = Counter(_tokenize(query))
        scored = [
            (article, _cosine(query_vector, Counter(_tokenize(self.document_text(article)))))
            for article in candidates
        ]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]

    def _fallback_related(
        self, article: Article, candidates: list[Article], limit: int
    ) -> list[RelatedArticle]:
        base = Counter(_tokenize(self.document_text(article)))
        related: list[RelatedArticle] = []
        for target in candidates:
            if target.id == article.id or target.id is None:
                continue
            score = _cosine(base, Counter(_tokenize(self.document_text(target))))
            shared = sorted(set(article.keywords) & set(target.keywords))
            if shared:
                score += 0.2
            related.append(
                RelatedArticle(
                    article_id=target.id,
                    title=target.title,
                    reason=self.reason(shared, target),
                    score=round(score, 3),
                    shared_keywords=shared,
                )
            )
        return sorted(related, key=lambda item: item.score, reverse=True)[:limit]

    @staticmethod
    def reason(shared: list[str], target: Article) -> str:
        if shared:
            return f"{', '.join(shared[:3])} 키워드를 공유합니다."
        return f"{target.category} 카테고리의 유사한 맥락입니다."

    @staticmethod
    def document_text(article: Article) -> str:
        return "\n".join(
            [
                article.title,
                article.description,
                article.summary_one_line,
                article.summary_three_lines,
                article.content_text[:1000],
                " ".join(article.keywords),
            ]
        )
