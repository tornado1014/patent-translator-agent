# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 참조하는 가이드입니다.

## 프로젝트 개요

영한 특허번역을 위한 4-에이전트 협업 시스템입니다.

### 핵심 기능
- 영문 특허 → 한국어 특허 번역
- 원문 오류 자동 검출 (참조부호, 용어 불일치)
- 섹션별 번역으로 긴 문서 처리
- 동적 Term Base로 용어 일관성 유지
- 95점 품질 기준 적용

## 스킬 트리거

다음 명령으로 특허번역 스킬을 활성화합니다:
- "특허 번역해줘"
- "/patent-translator"
- "patent translation"

## 에이전트 파일

| 에이전트 | 경로 | 역할 |
|----------|------|------|
| Source Analyzer | `.claude/agents/source-analyzer.md` | 용어 추출, 원문 오류 검출 |
| Patent Translator | `.claude/agents/patent-translator.md` | 번역 수행 |
| Translation Reviewer | `.claude/agents/translation-reviewer.md` | 품질 검토 (95점 기준) |
| Feedback Learner | `.claude/agents/feedback-learner.md` | 피드백 학습 |
| Terminology Conflict Resolver | `.claude/agents/terminology-conflict-resolver.md` | 도메인별 용어 충돌 해결 |

## 데이터 파일

| 파일 | 경로 | 용도 |
|------|------|------|
| 스타일 가이드 | `.claude/skills/patent-translator/data/style-guide.md` | 번역 규칙 |
| 용어집 | `.claude/skills/patent-translator/data/terminology-db.md` | 기본 용어 |
| 오류 패턴 | `.claude/skills/patent-translator/data/error-patterns.md` | 번역 오류 |
| 원문 오류 패턴 | `.claude/skills/patent-translator/data/source-error-patterns.md` | 원문 오류 |
| 피드백 로그 | `.claude/skills/patent-translator/data/feedback-log.md` | 피드백 이력 |

## 번역 워크플로우

1. **프로젝트 초기화**: `output/[project-name]/` 폴더 생성
2. **섹션 분할**: TAC → Background → Summary → Drawings → Detailed
3. **각 섹션**: Source Analyzer → Patent Translator → Translation Reviewer
4. **피드백 반영**: Feedback Learner가 데이터 파일 업데이트
5. **최종 출력**: 마크다운 병합 → 워드 변환

## 품질 기준

- **95점 이상**: 통과
- **95점 미만**: Patent Translator에게 재번역 지시 (최대 3회)

### 평가 항목
- 정확성 (50점)
- 용어 일관성 (25점)
- 스타일 준수 (15점)
- 유창성 (10점)

## 핵심 번역 규칙

### 상기 (Antecedent Basis)
- 첫 등장: 관사 생략 (a compound → 화합물)
- 이후 참조: 반드시 "상기" (the compound → **상기** 화합물)

### 전환구
- comprising → 포함하는 (Open-ended)
- consisting of → 이루어지는 (Closed-ended)

### 수량 범위 주의
- more than one → **둘 이상** (하나 이상 ❌)
- less than two → **하나 이하** (둘 이하 ❌)

## 출력 폴더 구조

```
output/[project-name]/
├── sections/           # 섹션별 번역
├── project-tb.md       # 동적 Term Base
├── source-error-report.md
├── translation-final.md
└── translation-final.docx
```

## 섹션 병합 규칙 (MANDATORY)

`output/*/sections/` 폴더의 파일을 병합할 때는 **반드시**:

1. `python .claude/skills/patent-translator/scripts/merge-sections.py output/[project] --json` 사용
2. `cat`, `Read+Write` 직접 병합 **금지**

이 규칙은 한국 특허 표준 섹션 순서를 보장합니다:
> 발명의 명칭 → 기술분야 → 배경기술 → 도면 → 상세설명 → 청구범위 → 요약서

**PreToolUse 훅이 `cat.*section.*\.md` 패턴을 감지하면 자동 차단됩니다.**

## 워드 변환

```bash
# 1단계: 섹션 병합 (필수)
python .claude/skills/patent-translator/scripts/merge-sections.py output/[project] --json

# 2단계: 워드 변환
python .claude/skills/patent-translator/scripts/convert-to-docx.py output/[project]/translation-final.md
```

포맷: 바탕체 12pt, 양쪽정렬, 1.5줄 간격

## Deep Interview 스킬

요구사항 정리 및 스펙 문서 완성을 위한 심층 인터뷰 스킬.
Anthropic 엔지니어 Thariq의 "인터뷰 프롬프트" 기반.

### 트리거 명령어
- `/deep-interview`
- `/deep-interview @SPEC.md`
- "심층 인터뷰해줘"
- "스펙 인터뷰"

### 워크플로우
1. **문서 & 코드 분석**: SPEC 문서 및 코드베이스 탐색
2. **심층 인터뷰**: 4개 카테고리별 질문
   - 기술적 구현 (아키텍처, 데이터 모델, API)
   - UI & UX (흐름, 인터페이스, 피드백)
   - 우려 사항 (보안, 성능, 확장성)
   - 트레이드오프 (복잡도 vs 성능, 시간 vs 품질)
3. **스펙 완성**: 인터뷰 내용 구조화 및 문서 업데이트

### 관련 파일
| 파일 | 경로 | 역할 |
|------|------|------|
| 스킬 정의 | `.claude/skills/deep-interview/SKILL.md` | 워크플로우 + 사용법 |
| 인터뷰어 에이전트 | `.claude/agents/deep-interviewer.md` | Opus 기반 질문 생성 |
| 질문 템플릿 | `.claude/skills/deep-interview/data/question-templates.md` | 4개 카테고리 질문 |

### 특징
- 맥락 기반 질문 (상투적 질문 금지)
- explore 에이전트로 코드베이스 자동 분석
- AskUserQuestion으로 대화형 인터뷰 진행
- 완성까지 계속 (사용자가 "완료" 선언 시 종료)
