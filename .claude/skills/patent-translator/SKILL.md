---
name: patent-translator
description: |
  영문 특허를 한국어로 번역합니다.
  특허 명세서, 청구항, 기술문서 번역 요청 시 자동으로 활성화됩니다.
  4개 에이전트(분석→번역→검토→학습) 협업 시스템입니다.
version: 1.0.0
trigger:
  - "특허 번역해줘"
  - "/patent-translator"
  - "patent translation"
dependencies:
  - python-docx
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

## 번역 예시 (Input/Output)

### 예시 1: 청구항 번역 (Method Claim)

**입력 (영문)**:
```text
1. A method of treating cancer in a patient in need thereof, comprising
administering to the patient a therapeutically effective amount of a compound
of Formula (I), wherein the compound is substantially amorphous.
```

**출력 (한국어)**:
```text
1. 암 치료를 필요로 하는 환자에서 암을 치료하는 방법으로서,
화학식 (I)의 화합물의 치료적 유효량을 상기 환자에게 투여하는 단계를 포함하고,
여기서 상기 화합물은 실질적으로 비정질인, 방법.
```

**처리 포인트**:
- `a patient` → `환자` (첫 등장, 부정형)
- `the patient` → `상기 환자` (재등장, 상기 삽입)
- `a compound` → `화합물` (첫 등장)
- `the compound` → `상기 화합물` (재등장)
- `comprising` → `포함하고` (개방형 전환구)

---

### 예시 2: 청구항 번역 (Composition Claim)

**입력 (영문)**:
```text
5. A pharmaceutical composition comprising:
(a) an antibody drug conjugate (ADC); and
(b) a pharmaceutically acceptable carrier,
wherein the ADC comprises a humanized antibody conjugated to a cytotoxic agent.
```

**출력 (한국어)**:
```text
5. 하기를 포함하는 약학적 조성물:
(a) 항체-약물 접합체 (ADC); 및
(b) 약학적으로 허용가능한 담체,
여기서 상기 ADC는 세포독성제에 접합된 인간화 항체를 포함한다.
```

**처리 포인트**:
- `antibody drug conjugate (ADC)` → `항체-약물 접합체 (ADC)` (약어 병기)
- `the ADC` → `상기 ADC` (재등장)
- `humanized antibody` → `인간화 항체` (전문 용어)
- 리스트 구조 `(a)`, `(b)` 유지

---

### 예시 3: 원문 오류 처리

**입력 (영문 - 오류 포함)**:
```text
[0045] The housing (10) is connected to the base (20).
[0067] The casing (10) provides structural support.
```

**Source Analyzer 출력** (`source-error-report.md`):
```markdown
## 참조부호 불일치 (Major)
| 위치 | 참조부호 | 문제 |
|------|----------|------|
| [0045] | 10 | "housing"으로 기술 |
| [0067] | 10 | "casing"으로 기술 → 통일 필요 |
```

**번역 출력** (주석 포함):
```text
[0045] 상기 하우징(10)은 베이스(20)에 연결된다.
[0067] 상기 케이싱(10) [원문 오류 - Major: [0045]에서 "housing"으로도 기술됨] 은
구조적 지지를 제공한다.
```

---

### 예시 4: 동적 TB 업데이트

**섹션 1 (Claims) 번역 후 project-tb.md**:
```markdown
## 핵심 용어 (Title/Abstract/Claims에서 확립)
| English | Korean | 첫 등장 | 비고 |
|---------|--------|---------|------|
| antibody drug conjugate | 항체-약물 접합체 | Claim 5 | ADC |
| humanized antibody | 인간화 항체 | Claim 5 | |
| therapeutically effective amount | 치료적 유효량 | Claim 1 | |
```

**섹션 2 (Background) 번역 후 추가**:
```markdown
## 배경기술 추가 용어 (섹션 2)
| English | Korean | 첫 등장 | 비고 |
|---------|--------|---------|------|
| prior art | 선행 기술 | [0003] | |
| conventional therapy | 종래 치료법 | [0005] | |
```

> **참고**: 동일 용어(예: `antibody drug conjugate`)가 섹션 2에서 다시 나타나면 TB에 추가하지 않고 기존 번역(`항체-약물 접합체`)을 그대로 사용합니다.

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

