# 260617_NEWSAGENT
IT News 요약 및 분석 에이전트

## MVP 실행

Python 기반 FastAPI 웹사이트입니다. News API, LangChain/OpenAI, Chroma를 사용할 수 있게 구성되어 있고, API 키가 없어도 샘플 기사로 화면을 확인할 수 있습니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다.

Chroma Vector DB까지 설치하려면 Python 3.11-3.13 환경에서 다음을 추가로 실행합니다. Python 3.14에서는 Chroma 하위 의존성의 네이티브 빌드가 실패할 수 있어 기본 앱은 로컬 유사도 검색 fallback으로 동작합니다.

```bash
pip install -r requirements-vector.txt
```

## 환경 변수

- `NEWS_API_KEY`: News API 키
- `OPENAI_API_KEY`: OpenAI API 키
- `OPENAI_MODEL`: 기사 요약/분석 모델, 기본값 `gpt-4o-mini`
- `OPENAI_EMBEDDING_MODEL`: 임베딩 모델, 기본값 `text-embedding-3-small`
- `DATABASE_PATH`: SQLite DB 경로
- `CHROMA_PATH`: Chroma 저장 경로
- `ARTICLES_PER_PAGE`: 그리드 페이지당 기사 수
- `NEWS_FETCH_LIMIT`: News API에서 유지할 한국어 기사 수, 기본값 `50`
- `INITIAL_FETCH_ON_STARTUP`: 첫 실행 시 News API 초기 기사 수집 여부
- `INITIAL_NEWS_COUNT`: 첫 화면용 초기 기사 수

## 주요 화면

- `/`: 대시보드
- `/news`: 에디토리얼 그리드 뉴스 목록
- `/article/{id}`: 기사 상세 분석
- `/keywords`: 키워드 분석
- `/sentiment`: 감정 분석
- `/search`: 의미 기반 검색
- `/status`: 수집/분석 상태
