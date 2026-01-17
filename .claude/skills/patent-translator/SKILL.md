---
name: patent-translator
description: |
  Translates English patents to Korean with 4-agent collaboration.
  Use when: patent translation, specification translation, claims translation,
  En-Ko technical document localization, 특허 번역, 영한 번역.
  Features: analyze→translate→review→learn loop, dynamic term base,
  95-point quality threshold, 2-stage review (mechanical + semantic).
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - Task
---

# 영한 특허번역 에이전트 (Patent Translator Skill)

> **버전**: 1.0.0
> **작성일**: 2026-01-10

---

## 개요

영문 특허를 한국어로 번역하는 4-에이전트 협업 시스템입니다.

### 핵심 특징
- **4개 에이전트 루프**: 분석 → 번역 → 검토 → 학습
- **동적 TB(Term Base)**: 섹션별 번역 시 실시간 용어 누적
- **원문 오류 검출**: 번역 전 원문의 참조부호/용어 불일치 검출
- **95점 품질 기준**: 특허의 법적 문서 특성 반영
- **2단계 검토**: 기계적 검토(스크립트) + 의미적 검토(에이전트)
- **워드 변환**: 바탕체 12pt, 양쪽정렬 자동 적용

---

## 훅 메시지 응답 규칙 (필수)

시스템 훅에서 다음 메시지가 출력되면 **반드시** 해당 동작을 수행해야 합니다.
이 규칙을 무시하면 워크플로우 위반으로 간주됩니다.

### [MECHANICAL_CHECK_PASSED] / [MECHANICAL_CHECK_FAILED]

섹션 파일 생성 시 `validate-translation.py` 스크립트가 자동 실행됩니다.

- **PASSED**: 기계적 검토 통과 → 의미적 검토(Translation Reviewer) 진행
- **FAILED**: 오류 목록 확인 후 번역 수정 → 재저장 → 재검사

### [FEEDBACK_REQUIRED]

섹션 번역 파일 생성 후 출력됩니다.

- **필수 동작**: AskUserQuestion으로 사용자에게 피드백 요청
- **질문 예시**: "이 섹션 번역에 수정이 필요하신가요?"
- **옵션 예시**:
  - 수정 필요 (구체적 피드백 입력)
  - 수정 없음, 다음 섹션 진행
  - 전체 재번역 필요
- **후속 처리**: 피드백 수신 시 Feedback Learner 실행

### [FINAL_REVIEW_REQUIRED]

translation-final.md 생성 후 출력됩니다.

- **필수 동작**: AskUserQuestion으로 최종 검토 요청
- **질문 예시**: "전체 번역 결과를 검토하시겠습니까?"
- **옵션 예시**:
  - 전체 승인, 워드 변환 진행
  - 특정 섹션 수정 필요 (섹션 번호 입력)
  - 전체 재검토 필요
- **후속 처리**: 승인 후에만 워드 변환 진행

---

## 2단계 검토 시스템

번역 품질 보장을 위해 기계적 검토와 의미적 검토를 분리합니다.

### 1단계: 기계적 검토 (Python 스크립트)

`scripts/validate-translation.py`가 자동 실행됩니다.

| 검사 항목 | 설명 |
|-----------|------|
| 참조부호 형식 | `명사(10)` (O), `명사 (10)` (X) |
| 청구항 구조 | 번호 연속성, 마침표 종결 |
| 서수 형식 | `제1`, `제2` (첫째, 둘째 X) |
| 전환구 일관성 | comprising → 포함하는 |
| 기본 상기 검사 | 재등장 시 상기 누락 여부 |
| 약어 형식 | 첫 등장 시 풀이 여부 |
| 숫자-단위 공백 | `10 mL` (O), `10mL` (X) |

### 2단계: 의미적 검토 (Translation Reviewer)

기계적 검토 통과 후 에이전트가 수행합니다.

| 검사 항목 | 설명 |
|-----------|------|
| 정확성 | 의미 왜곡, 누락, 첨가 |
| 유창성 | 자연스러운 한국어 표현 |
| 문맥 판단 | 복잡한 상기 판단, 도메인 적합성 |
| 스타일 | 청구항 어미, 전문 용어 선택 |

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
| **2** | 배경기술 | Background | 2,500단어 초과 시 분할 |
| **3** | 발명의 내용 | Summary | 2,500단어 초과 시 분할 |
| **4** | 도면의 간단한 설명 | Brief Description of Drawings | 단독 처리 |
| **5** | 상세 설명 | Detailed Description | **2,500단어 단위** 분할 |

### 3. 각 섹션 처리 흐름 (Task 도구로 서브에이전트 호출)

각 단계는 **Task 도구**로 서브에이전트를 호출하여 실행합니다.

**Step 1: Source Analyzer**
```
Task(subagent_type="source-analyzer", prompt="프로젝트: [name], 원문: [path]")
  → terminology-analysis.md, source-error-report.md, project-tb.md
```

**Step 2: Patent Translator**
```
Task(subagent_type="patent-translator", prompt="프로젝트: [name], 섹션: [N]")
  → section-NN-[name].md
  → [훅 트리거: validate-translation.py + FEEDBACK_REQUIRED]
```

**Step 3: Translation Reviewer**
```
Task(subagent_type="translation-reviewer", prompt="검토: section-NN.md")
  → 95점 미만: Step 2 재호출 (최대 3회)
  → 95점 이상: 통과
```

**Step 4: 피드백 수집** (AskUserQuestion)
```
사용자 피드백 요청 → 피드백 있을 경우:
Task(subagent_type="feedback-learner", prompt="피드백: [내용]")
  → project-tb.md, terminology-db.md 업데이트
```

**→ 섹션 N+1로 진행**

### 4. 최종 통합 및 변환

> **주의**: 아래 TOKEN LIMIT GUARD 규칙을 반드시 준수해야 합니다.

```
모든 섹션 완료
    │
    ▼
Python 스크립트로 병합 (Claude 직접 병합 금지)
    │
    ▼
메타데이터 검증 (파일 내용 읽지 않음)
    │
    ▼
워드 변환
    │
    ▼
사용자에게 결과 보고 (메타데이터만)
```

---

## TOKEN LIMIT GUARD: 섹션 병합 규칙

대용량 특허 문서 번역 시 토큰 제한 문제를 방지하기 위한 **필수 규칙**입니다.

### 금지 행위

Claude는 다음 행위를 **절대** 수행하지 않습니다:

| 금지 | 설명 |
|------|------|
| 모든 섹션 읽기 후 Write | 섹션 파일들을 모두 읽어서 하나의 파일로 직접 작성 |
| translation-final.md 읽기 | 병합된 파일의 전체 내용을 Read 도구로 읽기 |
| 수동 연결 | 섹션 내용을 복사-붙여넣기로 연결 |

### 허용 행위

| 허용 | 설명 |
|------|------|
| Python 스크립트 실행 | `merge-sections.py`, `verify-merge.py`, `convert-to-docx.py` |
| 메타데이터 확인 | 스크립트 출력의 JSON/텍스트 리포트 확인 |
| 개별 섹션 읽기 | 특정 섹션 수정/검토 시 해당 파일만 읽기 |

### 병합 워크플로우

```bash
# Step 1: 섹션 병합 (Python)
python scripts/merge-sections.py output/[project] --json

# Step 2: 병합 검증 (Python)
python scripts/verify-merge.py output/[project]/translation-final.md

# Step 3: 워드 변환 (Python)
python scripts/convert-to-docx.py output/[project]/translation-final.md
```

### 사용자 보고 형식

병합 완료 시 Claude가 사용자에게 보고하는 내용 (메타데이터만):

```
번역 병합이 완료되었습니다.

병합 결과:
- 섹션 수: 6개
- 총 라인 수: 310줄
- 파일 크기: 76,234 bytes

출력 파일:
- translation-final.md (마크다운)
- translation-final.docx (Word)

모든 섹션이 정상적으로 포함되었습니다.
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
├── chunk-context.md           # 청크 간 컨텍스트 (작업 기억)
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

## 청크 간 컨텍스트 (chunk-context.md)

긴 섹션을 분할 번역할 때 **참조부호 일관성**과 **상기 추적**을 유지하기 위한 작업 기억 파일입니다.

### 역할 분담

| 파일 | 용도 | 지속성 |
|------|------|--------|
| **project-tb.md** | 확정 용어집 (프로젝트 전체) | 영구 |
| **chunk-context.md** | 청크 간 임시 컨텍스트 | 번역 중만 |

### 파일 구조

```markdown
# 청크 간 컨텍스트

## 참조부호 매핑

| 번호 | 영문 | 한글 | 첫 등장 |
|------|------|------|---------|
| 10 | housing | 하우징 | [0012] |
| 20 | base | 베이스 | [0012] |
| 100 | memory subsystem | 메모리 서브시스템 | Claim 1 |

## 핵심 명사 상기 상태

| 명사 | 첫 등장 | 상기 필요 |
|------|---------|-----------|
| 메모리 서브시스템 | Claim 1 | O |
| 호스트 시스템 | Claim 1 | O |

## 이전 청크 마지막 문단 (오버랩용)

> [0045] 상기 컨트롤러(30)는 상기 메모리 컴포넌트와 통신한다.
```

### 워크플로우

```
[청크 N 번역 시작]
    │
    ├→ chunk-context.md 로드 (이전 상태)
    ├→ project-tb.md 로드 (확정 용어)
    │
    ▼
Patent Translator 번역 수행
    │
    ▼
chunk-context.md 업데이트
    ├→ 새 참조부호 추가
    ├→ 새 핵심 명사 추가
    └→ 마지막 문단 갱신
    │
    ▼
[청크 N+1로 진행]
```

### 생성 시점

- **Source Analyzer**: 첫 섹션 분석 시 chunk-context.md 초기 생성
- **Patent Translator**: 각 청크 번역 완료 후 업데이트

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

- **기본**: `특허 번역해줘` + 원문 파일 경로 제공
- **섹션별**: `Claims 부분만 먼저 번역해줘`
- **피드백**: `"substrate"는 "기재"로 번역해줘` → terminology-db.md 자동 업데이트

---

## 번역 예시

> **상세 예시**: `data/translation-examples.md` 참조

핵심 처리 포인트:
- `a/an + 명사` → 부정형 (첫 등장)
- `the + 명사` → `상기 + 명사` (재등장)
- `comprising` → `포함하는/포함하고` (개방형)
- 약어: `영문 풀이 (ABBR)` → `한글 풀이 (ABBR)`

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

## GitHub 연동 (선택적)

```bash
git add .claude/skills/patent-translator/data/
git commit -m "Update: terminology and feedback from [project]"
```

---

## 에러 처리

### 번역 품질 미달 (max-retry 에스컬레이션)

품질 게이트(95점)를 통과하지 못한 경우의 에스컬레이션 로직입니다.

```
재번역 시도 1회차
    │
    └→ 95점 미달 → Patent Translator 재호출 (피드백 포함)
    │
재번역 시도 2회차
    │
    └→ 95점 미달 → Patent Translator 재호출 (누적 피드백)
    │
재번역 시도 3회차 (최종)
    │
    └→ 95점 미달 → **사용자 에스컬레이션** (자동 재번역 중단)
```

#### 에스컬레이션 시 필수 동작

3회 재번역 후에도 95점 미달인 경우:

1. **AskUserQuestion**으로 사용자에게 판단 요청
2. 아래 메시지와 옵션 제공:

```
메시지: "3회 재번역 후에도 95점 미달입니다. 수동 검토가 필요합니다."

옵션:
- 현재 상태로 승인 (점수 표시: XX점)
- 특정 부분 직접 수정 후 진행
- 전체 재번역 (다른 접근 방식 요청)
- 번역 중단, 원문 확인 필요
```

3. 사용자 선택에 따라 후속 처리:
   - **승인**: 다음 섹션으로 진행 (점수 기록)
   - **직접 수정**: 사용자 수정 대기 → 재검토
   - **전체 재번역**: retry 카운터 리셋, 다른 지시사항 반영
   - **번역 중단**: 워크플로우 일시 정지

#### 재번역 시 피드백 누적

각 재번역 시도 시 이전 리뷰 피드백을 누적하여 Patent Translator에게 전달:

```
Task(subagent_type="patent-translator", prompt="""
프로젝트: [name]
섹션: [N]
재번역 시도: [2/3]

[이전 피드백]
- 1회차: 상기 누락 5건, 참조부호 형식 오류 2건
- 2회차: 상기 누락 2건

집중 개선 항목: 상기 누락 (잔여 2건)
""")
```

### 원문 분할 실패
- 사용자에게 섹션 구분 요청
- 수동으로 섹션 지정 후 진행

### 용어 충돌
- 사용자에게 선택 요청
- 선택된 용어로 project-tb.md 업데이트

---

## Word 피드백 임포트 (Track Changes)

검토자가 Word에서 Track Changes로 피드백을 남기면, 이를 자동으로 추출하여 학습 데이터에 반영할 수 있습니다.

### 사용 시나리오

1. 번역된 `.docx` 파일을 검토자에게 전달
2. 검토자가 **Track Changes + Comments**로 피드백 작성
3. 피드백이 담긴 `.docx` 파일 수신
4. `/import-feedback-docx`로 피드백 추출
5. 승인 보고서 검토 및 체크박스 선택
6. `/apply-feedback-docx`로 데이터 파일 업데이트

### 명령어

| 명령 | 설명 |
|------|------|
| `/import-feedback-docx <docx> [project]` | Track Changes/Comments 추출 및 보고서 생성 |
| `/apply-feedback-docx <project>` | 승인된 피드백을 데이터 파일에 반영 |

### 자동 분류 규칙

| 유형 | 분류 기준 | 대상 파일 |
|------|-----------|-----------|
| **terminology** | 용어 대체, 단어 수준 변경 | terminology-db.md, project-tb.md |
| **error** | 상기 누락, 참조부호 오류 | error-patterns.md |
| **style** | 표현 개선, 자연스러움 | feedback-log.md |
| **other** | 기타 피드백 | feedback-log.md |

### 워크플로우 다이어그램

```
reviewed.docx (Track Changes ON)
    │
    ▼
/import-feedback-docx
    │
    ├→ Track Changes 추출 (w:ins, w:del)
    ├→ Comments 추출 (w:comment)
    ├→ 자동 분류 (terminology, error, style, other)
    │
    ▼
feedback-review-report.md (체크박스 승인)
    │
    ▼
/apply-feedback-docx
    │
    ├→ terminology-db.md 업데이트
    ├→ error-patterns.md 업데이트
    ├→ project-tb.md 업데이트
    └→ feedback-log.md 로깅
```

### 생성 파일

| 파일 | 설명 |
|------|------|
| `feedback-extracted.json` | 추출된 원시 데이터 |
| `feedback-classified.json` | 분류된 피드백 데이터 |
| `feedback-review-report.md` | 체크박스 기반 승인 보고서 |

### 주의사항

- **Track Changes가 꺼진 상태**로 저장된 파일은 변경 사항을 추출할 수 없습니다.
- 변경 사항을 **"모두 승인"** 또는 **"모두 거절"**한 후 저장하면 추출이 불가능합니다.
- 승인 보고서에서 `[ ]`를 `[x]`로 변경해야 반영됩니다.

### CLI 스크립트

```bash
# 피드백 추출
python scripts/docx_feedback_cli.py import <docx-path> --project <name>

# 피드백 적용
python scripts/docx_feedback_cli.py apply <project-name>

# 상태 확인
python scripts/docx_feedback_cli.py status <project-name>
```


