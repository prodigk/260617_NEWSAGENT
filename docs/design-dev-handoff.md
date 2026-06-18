# designk 개발 전달 지침

## 개발 목표

`devk`는 `docs/site-plan.md`의 기능과 `docs/design-guidelines.md`의 디자인 지침을 함께 기준으로 MVP 화면 구조를 구현합니다.

우선순위는 다음과 같습니다.

1. 대시보드
2. 뉴스 목록
3. 뉴스 상세
4. 키워드 분석
5. 감정 분석
6. 의미 검색
7. 수집 상태

## 레이아웃 구현 기준

- 전체 앱은 크림색 지면 위의 에디토리얼 그리드로 구성합니다.
- 데스크톱에서는 12컬럼 기반, 주요 화면은 3영역 구조를 사용합니다.
- 카드 그림자보다 얇은 `1px` 구분선과 여백으로 영역을 나눕니다.
- 뉴스 목록은 첨부 이미지처럼 한 페이지를 하나의 편집 지면으로 보고, 페이지네이션으로 지면을 전환합니다.
- 한 그리드 페이지에는 기본 6-10개 기사를 배치합니다.
- 모바일에서는 단일 컬럼으로 전환하고, 필터는 접이식 패널 또는 드로어로 처리합니다.

## 우선 구현 컴포넌트

- `AppHeader`
- `RefreshNewsButton`
- `CollectionStatus`
- `ArticleTeaser`
- `ArticleList`
- `KeywordHighlight`
- `KeywordCloud`
- `SentimentLabel`
- `SentimentSummary`
- `AnalysisStrip`
- `RelatedArticleList`
- `SemanticSearchBox`
- `JobTimeline`
- `EmptyState`
- `ErrorState`
- `LoadingState`
- `EditorialGrid`
- `EditorialSlot`
- `Pagination`
- `SourceProfile`

## 데이터 상태 매핑

### 수집 상태

- `idle`: 아직 수집 전
- `collecting`: News API 수집 중
- `extracting`: 원문 URL 본문 추출 중
- `analyzing`: LangChain/OpenAI 분석 중
- `embedding`: OpenAI 임베딩 생성 및 Chroma 저장 중
- `completed`: 수집/분석 완료
- `partial_failed`: 일부 기사 실패
- `failed`: 전체 수집 실패

### 기사 분석 상태

- `pending`: 분석 대기
- `summarized`: 요약 완료
- `keyworded`: 키워드 분석 완료
- `sentimented`: 감정 분석 완료
- `embedded`: Chroma 저장 완료
- `failed`: 분석 실패

## 화면별 구현 메모

### 대시보드

- 상단 헤더 우측에 `최근기사 불러오기` 버튼을 둡니다.
- 첫 화면 안에 수집 상태, 대표 기사, 상위 키워드, 감정 분포가 함께 보여야 합니다.
- 대표 기사는 큰 세리프 제목과 3줄 요약으로 강조합니다.

### 뉴스 목록

- 필터는 카테고리, 키워드, 감정, 출처, 정렬 순서로 구성합니다.
- 기본 보기는 에디토리얼 그리드입니다.
- 사용자가 페이지네이션 숫자를 누르면 해당 페이지의 기사 묶음으로 그리드를 다시 배치합니다.
- 리스트 아이템 또는 그리드 슬롯은 분석 상태와 관련기사 수를 함께 표시합니다.
- 키워드와 감정 라벨은 클릭 가능한 필터 트리거로 구현합니다.
- 필터, 검색, 정렬 조건이 바뀌면 페이지 번호는 1로 초기화합니다.
- 페이지 이동만 할 때는 필터, 검색, 정렬 조건을 유지합니다.

### 에디토리얼 그리드

- `EditorialGrid`는 기사 배열과 현재 페이지 번호를 받아 해당 페이지의 슬롯 배열을 렌더링합니다.
- 페이지당 기사 수는 데스크톱 10개를 기본값으로 시작합니다.
- 총 50개 기사 기준으로 약 5개 페이지가 생성됩니다.
- 슬롯 타입은 `hero`, `feature`, `brief`, `related`를 사용합니다.
- `hero` 슬롯에는 이미지가 있는 기사와 높은 중요도/관련도 점수를 가진 기사를 우선 배치합니다.
- 이미지가 없는 기사는 `brief` 또는 타이포그래피 중심 슬롯에 우선 배치합니다.
- `related` 슬롯은 현재 페이지의 대표 기사 기준 관련기사 2-3개를 표시합니다.

초기 슬롯 예시:

```text
page[0]
- slot 1: hero, article 1, columns 1-2
- slot 2: feature, article 2, column 3
- slot 3: feature, article 3, column 4
- slot 4: brief, article 4
- slot 5: brief, article 5
- slot 6: feature, article 6
- slot 7: brief, article 7
- slot 8: related, hero article recommendations
- slot 9: brief, article 8
```

### 페이지네이션

- `Pagination`은 총 기사 수, 페이지당 기사 수, 현재 페이지, 페이지 변경 콜백을 받습니다.
- 데스크톱에서는 `1 2 3 4 5 ...` 숫자 페이지네이션을 표시합니다.
- 현재 페이지는 `aria-current="page"`를 적용합니다.
- 페이지 버튼은 키보드로 이동 가능해야 합니다.
- 모바일에서는 이전/다음과 현재 페이지를 중심으로 간소화할 수 있습니다.
- 페이지 변경 시 그리드 상단으로 스크롤합니다.

### 뉴스 상세

- 요약과 분석을 원문보다 먼저 보여줍니다.
- 원문 링크는 제목 근처에 항상 노출합니다.
- 관련기사 추천에는 추천 이유와 공통 키워드를 표시합니다.

### 키워드 분석

- 상위 키워드는 하이라이트 텍스트와 기사 수를 함께 보여줍니다.
- 키워드 클릭 시 관련 기사 목록이 갱신되어야 합니다.

### 감정 분석

- 긍정/중립/부정 비율과 대표 기사를 함께 보여줍니다.
- 색상만으로 감정을 구분하지 말고 텍스트 라벨을 항상 포함합니다.

### 의미 검색

- 자연어 검색 입력과 검색 예시를 제공합니다.
- 검색 결과에는 관련도와 매칭 키워드를 함께 표시합니다.

### 수집 상태

- News API, 본문 추출, OpenAI 분석, Chroma 저장 단계를 타임라인으로 보여줍니다.
- 실패 기사 목록에는 실패 단계와 사유를 표시합니다.

## 스타일 토큰 구현

초기 CSS 변수 예시:

```css
:root {
  --surface-paper: #f5f0e8;
  --surface-panel: #fbf8f1;
  --surface-raised: #fffdf8;
  --ink-primary: #111111;
  --ink-secondary: #3e3a35;
  --ink-muted: #7a736a;
  --line-subtle: #ddd4c8;
  --line-strong: #111111;
  --accent-peach: #ffb59d;
  --accent-yellow: #f6e36d;
  --accent-mint: #c8e8e8;
  --accent-positive: #52fd97;
  --accent-neutral: #5fb4ff;
  --accent-negative: #d24646;
}
```

## 검증 포인트

- 데스크톱에서 첫 화면의 3영역 구조가 유지되는지 확인합니다.
- 뉴스 목록에서 페이지네이션을 눌렀을 때 그리드 내용이 해당 페이지 기사로 바뀌는지 확인합니다.
- 필터 적용 후 페이지네이션 총 페이지 수가 다시 계산되는지 확인합니다.
- 50개 기사 기준으로 마지막 페이지가 빈 슬롯 없이 자연스럽게 보이는지 확인합니다.
- 모바일에서 제목, 버튼, 필터, 하이라이트 텍스트가 겹치지 않는지 확인합니다.
- 데이터가 0개, 50개 미만, 50개일 때 모두 화면이 깨지지 않아야 합니다.
- News API 실패, 본문 추출 실패, OpenAI 실패, Chroma 실패 상태가 각각 구분되어야 합니다.
- 이미지가 없는 기사도 레이아웃이 어색하지 않아야 합니다.

## 뉴스 수집 필드 요구사항

그리드형 레이아웃을 완성도 있게 구현하려면 News API와 URL 본문 추출 단계에서 다음 필드를 최대한 확보합니다.

### 필수 필드

- `title`: 기사 제목
- `url`: 원문 기사 URL
- `source_name`: 출처명
- `published_at`: 발행일
- `description`: News API가 제공하는 요약/설명
- `content_text`: 원문 URL에서 추출한 본문
- `category`: IT, AI, 보안, 클라우드 등 분류

### 시각 배치용 필드

- `image_url`: 기사 대표 이미지
- `image_alt`: 이미지 대체 텍스트
- `image_source`: 이미지 출처 또는 크레딧
- `has_image`: 이미지 사용 가능 여부
- `display_weight`: 대표 기사/중간 기사/짧은 기사 배치를 위한 가중치

### 출처/프로필 필드

- `source_id`: 출처 ID
- `source_url`: 출처 홈페이지 또는 기사 출처 URL
- `source_profile_image_url`: 출처 로고 또는 프로필 이미지
- `source_description`: 출처 설명
- `author_name`: 작성자명
- `author_profile_image_url`: 작성자 프로필 이미지

### 분석 표시용 필드

- `summary_one_line`: 한 줄 요약
- `summary_three_lines`: 3줄 요약
- `keywords`: 핵심 키워드 배열
- `sentiment_label`: 긍정/중립/부정
- `sentiment_score`: 감정 점수
- `related_count`: 관련기사 수
- `analysis_status`: 분석 상태

### 누락 대응

- `image_url`이 없으면 타이포그래피 중심 슬롯으로 배치합니다.
- `source_profile_image_url`이 없으면 출처명 첫 글자 또는 단순 텍스트 마크를 표시합니다.
- `content_text` 추출에 실패하면 `description`을 분석 입력으로 사용하고 추출 실패 상태를 표시합니다.
- `author_name`이 없으면 작성자 영역을 생략하고 출처명을 우선 표시합니다.
