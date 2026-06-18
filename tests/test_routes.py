from fastapi.testclient import TestClient

from app.main import app
from app.models import Article


def article(index: int) -> Article:
    return Article(
        id=index,
        title=f"페이지 기사 {index}",
        url=f"https://example.com/{index}",
        source_name="테스트",
        published_at="2026-06-17T00:00:00Z",
        display_weight=100 - index,
        summary_three_lines=f"요약 {index}",
    )


def test_dashboard_uses_page_query(monkeypatch):
    articles = [article(index) for index in range(1, 13)]

    monkeypatch.setattr("app.main.list_articles", lambda *_, **__: articles)
    monkeypatch.setattr("app.main.latest_job", lambda: None)

    response = TestClient(app).get("/?page=2")

    assert response.status_code == 200
    assert 'class="page-title"' in response.text
    assert "Latest IT Brief" in response.text
    assert "페이지 기사 11" in response.text
    assert "페이지 기사 10" not in response.text
    assert "Collection Status" not in response.text
    assert "Top Keywords" not in response.text
