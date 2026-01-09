# 영한 특허번역 에이전트 (Patent Translator Skill)

> **트리거**: "특허 번역해줘", "/patent-translator", "patent translation"
> **버전**: 1.0
> **작성일**: 2026-01-10

---

## 개요

영문 특허를 한국어로 번역하는 4-에이전트 협업 시스템입니다.

### 핵심 특징
- **4개 에이전트 루프**: 분석 → 번역 → 검토 → 학습
- **동적 TB(Term Base)**: 섹션별 번역 시 실시간 용어 누적
- **원문 오류 검출**: 번역 전 원문의 참조부호/용어 불일치 검출
- **95점 품질 기준**: 특허의 법적 문서 특성 반영
- **워드 변환**: 바탕체 12pt, 양쪽정렬 자동 적용

---

## 에이전트 구성

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 입력 (원문)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  [1] Source Analyzer                                        │
│  - 용어 추출 + 도메인 식별                                    │
│  - 원문 오류 검출                                            │
│  - project-tb.md 초기화 (섹션 1)                             │
│                                                             │
│  출력: terminology-analysis.md, source-error-report.md      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  [2] Patent Translator                                      │
│  - 스타일 가이드 기반 번역                                    │
│  - 용어 일관성 유지 (project-tb.md 참조)                      │
│  - 원문 오류 주석 처리                                        │
│                                                             │
│  출력: section-XX-[name].md                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  [3] Translation Reviewer                                   │
│  - 품질 평가 (100점 만점)                                    │
│  - 상기/용어/스타일 검사                                      │
│  - 95점 미만 → [2]로 반환                                    │
│                                                             │
│  출력: review-report-section-XX.md                          │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌────────┴────────┐
                    │                 │
               95점 미만          95점 이상
                    │                 │
                    ▼                 ▼
            [2]로 반환          다음 섹션 진행
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│  [4] Feedback Learner (섹션 완료 후 또는 사용자 피드백 시)    │
│  - project-tb.md 업데이트                                   │
│  - terminology-db.md / error-patterns.md 업데이트            │
│  - feedback-log.md 기록                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    [모든 섹션 완료 시]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  파일 통합 + 워드 변환                                       │
│  - sections/*.md → translation-final.md                    │
│  - translation-final.md → translation-final.docx           │
└─────────────────────────────────────────────────────────────┘
```

---

## 워크플로우

### 1. 프로젝트 초기화

```
사용자: "특허 번역해줘" + 원문 파일 제공
시스템:
  1. 프로젝트 폴더 생성: output/[project-name]/
  2. sections/ 하위 폴더 생성
  3. 원문 섹션 분할 (자동 또는 사용자 지정)
```

### 2. 섹션별 번역 순서

| 순서 | 섹션 | 영문명 | 처리 방식 |
|------|------|--------|-----------|
| **1** | 발명의 명칭 + 요약 + 청구범위 | Title + Abstract + Claims | **한 번에 처리** (핵심 용어 확립) |
| **2** | 배경기술 | Background | 단독 처리 |
| **3** | 발명의 내용 | Summary | 5,000단어 초과 시 분할 |
| **4** | 도면의 간단한 설명 | Brief Description of Drawings | 단독 처리 |
| **5** | 상세 설명 | Detailed Description | 5,000단어 단위 분할 |

### 3. 각 섹션 처리 흐름

```
[섹션 N 시작]
    │
    ▼
Source Analyzer 실행
    ├→ terminology-analysis.md 생성
    ├→ source-error-report.md 생성 (오류 있을 경우)
    └→ project-tb.md 업데이트 (신규 용어)
    │
    ▼
Patent Translator 실행
    └→ section-NN-[name].md 생성
    │
    ▼
Translation Reviewer 실행
    ├→ 95점 미만: Patent Translator에게 반환 (최대 3회)
    └→ 95점 이상: 통과
    │
    ▼
Feedback Learner 실행
    └→ project-tb.md 업데이트 (번역 확정 용어)
    │
    ▼
[섹션 N 완료 → 섹션 N+1로 진행]
```

### 4. 최종 통합 및 변환

```
모든 섹션 완료
    │
    ▼
섹션 파일 병합 (순서대로)
    │
    ▼
translation-final.md 생성
    │
    ▼
워드 변환 (python-docx 사용)
    │
    ▼
translation-final.docx 생성
    │
    ▼
사용자에게 전달
```

---

## 파일 구조

### 프로젝트별 출력
```
output/[project-name]/
├── sections/
│   ├── section-01-title-abstract-claims.md
│   ├── section-02-background.md
│   ├── section-03-summary.md
│   ├── section-04-drawings.md
│   ├── section-05a-detailed-part1.md  (분할 시)
│   ├── section-05b-detailed-part2.md
│   └── section-05c-detailed-part3.md
├── project-tb.md              # 동적 TB (실시간 누적)
├── terminology-analysis.md    # 용어 분석 결과
├── source-error-report.md     # 원문 오류 보고서
├── review-report-section-XX.md # 검토 보고서
├── translation-final.md       # 통합 마크다운
└── translation-final.docx     # 최종 워드 파일
```

### 참조 데이터
```
data/
├── style-guide.md            # 스타일 가이드
├── terminology-db.md         # 기본 용어집
├── error-patterns.md         # 번역 오류 패턴
├── source-error-patterns.md  # 원문 오류 패턴
├── feedback-log.md           # 피드백 로그
├── samples/                  # 번역 샘플
└── approved-translations/    # 승인된 번역
```

---

## 품질 기준

### 95점 임계값
특허는 법적 문서로서 높은 정확도를 요구합니다.

| 항목 | 배점 | 비고 |
|------|------|------|
| 정확성 | 50점 | 의미 정확성, 누락/첨가 |
| 용어 일관성 | 25점 | 상기 누락, TB 미준수 |
| 스타일 준수 | 15점 | 청구항 구조, 구두점 |
| 유창성 | 10점 | 자연스러운 한국어 |

### TAC 섹션 가중치
- Claims: x1.5
- Abstract: x1.3
- Title: x1.2

---

## 동적 TB 메커니즘

### 초기화 (섹션 1)
```markdown
# Project Term Base
**프로젝트**: [project-name]
**최종 업데이트**: [날짜] (섹션 1 완료 후)

## 핵심 용어 (Title/Abstract/Claims에서 확립)
| English | Korean | 첫 등장 | 비고 |
|---------|--------|---------|------|
| antibody drug conjugate | 항체-약물 접합체 | Claims 1 | ADC |
```

### 누적 업데이트 (섹션 2~N)
```markdown
## [섹션명] 추가 용어 (섹션 N)
| English | Korean | 첫 등장 | 비고 |
|---------|--------|---------|------|
| prior art | 선행 기술 | [0003] | |
```

### 중복 제거 규칙
- 동일 용어가 이미 존재하면 skip
- 번역이 다르면 충돌 보고 (사용자 판단)

---

## 워드 변환 설정

### 포맷
- **폰트**: 바탕체 (Batang)
- **폰트 크기**: 12pt
- **문단 정렬**: 양쪽 정렬 (Justify)
- **줄 간격**: 1.5줄

### 변환 스크립트
`scripts/convert-to-docx.py` 사용

```bash
python scripts/convert-to-docx.py output/[project]/translation-final.md
```

---

## 사용 예시

### 기본 사용
```
사용자: 특허 번역해줘
시스템: 원문 파일 경로를 알려주세요.
사용자: /path/to/patent.txt
시스템: [번역 시작...]
```

### 섹션별 번역
```
사용자: Claims 부분만 먼저 번역해줘
시스템: [Claims 섹션 번역 시작...]
```

### 피드백 제공
```
사용자: "substrate"는 화학 분야니까 "기재"로 번역해줘
시스템: [terminology-db.md 업데이트 완료]
        다음 번역부터 "substrate"를 "기재"로 번역합니다.
```

---

## 원문 오류 처리

Source Analyzer가 검출한 오류에 대해:

1. **source-error-report.md** 생성하여 사용자에게 제공
2. Patent Translator가 해당 부분에 `[원문 오류]` 주석 삽입
3. 사용자 확인 후 처리 방법 결정

---

## 학습 루프

```
번역 완료 → 사용자 피드백 → Feedback Learner
    │
    ├→ terminology-db.md 업데이트
    ├→ error-patterns.md 업데이트
    └→ source-error-patterns.md 업데이트
    │
    ▼
다음 번역 시 업데이트된 데이터 참조
```

---

## GitHub 연동

### 데이터 커밋 (선택적)
```bash
git add .claude/skills/patent-translator/data/
git commit -m "Update: terminology and feedback from [project]"
git push
```

### 모바일 사용
Claude 모바일 앱에서 GitHub 저장소 연결 후 동일하게 사용 가능

---

## 에러 처리

### 번역 품질 미달 (3회 연속)
- 사용자에게 판단 요청
- 수동 수정 후 진행

### 원문 분할 실패
- 사용자에게 섹션 구분 요청
- 수동으로 섹션 지정 후 진행

### 용어 충돌
- 사용자에게 선택 요청
- 선택된 용어로 project-tb.md 업데이트

