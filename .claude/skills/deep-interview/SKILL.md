---
name: deep-interview
description: |
  Deep interview skill for comprehensive spec refinement.
  Analyzes SPEC documents and codebase, then conducts thorough interviews
  covering technical implementation, UI/UX, concerns, and trade-offs.
  Use when: deep interview, 심층 인터뷰, spec interview, 스펙 인터뷰,
  requirements gathering, 요구사항 정리, interview me, 인터뷰해줘
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Task
  - AskUserQuestion
---

# Deep Interview Skill

Anthropic 엔지니어 Thariq의 "인터뷰 프롬프트"를 기반으로 한 심층 인터뷰 스킬.
SPEC 문서와 코드베이스를 분석하여 사용자와 심층 인터뷰를 진행하고, 완성된 스펙을 출력합니다.

## 트리거 명령어

- `/deep-interview`
- `/deep-interview @SPEC.md`
- "심층 인터뷰해줘"
- "스펙 인터뷰"

## 워크플로우

### Phase 1: 문서 & 코드베이스 분석

1. **문서 로딩**: 사용자가 지정한 SPEC 문서 읽기
   - `@SPEC.md` 형식으로 파일 지정
   - 지정하지 않으면 루트의 SPEC.md 또는 README.md 탐색

2. **코드베이스 탐색**: Task(explore) 에이전트로 분석
   - 관련 파일, 패턴, 아키텍처 파악
   - 기존 구현과 스펙의 갭 식별

3. **인터뷰 질문 생성**: 분석 결과를 바탕으로 맥락 기반 질문 준비

### Phase 2: 심층 인터뷰 루프

4개 카테고리별로 AskUserQuestion 도구를 사용하여 질문:

| 카테고리 | 질문 초점 |
|----------|-----------|
| **기술적 구현** | 아키텍처, 데이터 모델, API 설계, 의존성, 상태 관리 |
| **UI & UX** | 사용자 흐름, 인터페이스, 접근성, 반응성, 에러 처리 |
| **우려 사항** | 보안, 성능, 확장성, 유지보수성, 엣지 케이스 |
| **트레이드오프** | 복잡도 vs 성능, 시간 vs 품질, 단순성 vs 유연성 |

**인터뷰 규칙**:
- 뻔하거나 상투적인 질문 금지
- 문서/코드에서 발견한 구체적 맥락 기반 질문
- 한 번에 1-4개 질문 (AskUserQuestion 제한)
- 사용자가 "완료", "끝", "done" 선언할 때까지 계속

### Phase 3: 스펙 완성

인터뷰 완료 후 출력 옵션 선택:

- **옵션 A**: 원본 문서 업데이트 - 기존 SPEC 파일 직접 수정
- **옵션 B**: 새 문서 생성 - `SPEC-final.md` 또는 지정 파일명

출력 문서에는 인터뷰 내용이 구조화되어 포함됩니다:
- 명확해진 요구사항
- 결정된 기술적 선택
- 식별된 우려 사항과 해결책
- 합의된 트레이드오프

## 인터뷰 에이전트 호출

```
Task(deep-interviewer): {
  "spec_file": "<spec 파일 경로>",
  "codebase_context": "<탐색 결과 요약>"
}
```

## 질문 생성 원칙

### DO (해야 할 것)
- 문서에서 누락되거나 모호한 부분 식별하여 질문
- 코드베이스의 기존 패턴과 충돌 가능성 질문
- 구체적인 시나리오 기반 질문 ("X 상황에서 Y가 발생하면?")
- 숨겨진 가정 발견 질문 ("Z를 전제로 하셨나요?")

### DON'T (하지 말아야 할 것)
- "목표가 무엇인가요?" 같은 상투적 질문
- 문서에 이미 명시된 내용 재질문
- 한 번에 너무 많은 질문 (4개 초과)
- 예/아니오로만 답할 수 있는 단순 질문

## 예시 인터뷰 흐름

**1라운드 - 기술적 구현**:
```
Q1: "인증 시스템에서 JWT 토큰의 만료 시간이 명시되지 않았습니다.
    보안과 UX 사이에서 어떤 균형을 원하시나요?"

Q2: "현재 코드베이스에서 상태 관리를 Context API로 하고 있는데,
    새 기능도 동일하게 할지, Redux로 마이그레이션할지 결정이 필요합니다."
```

**2라운드 - UI & UX**:
```
Q1: "데이터 로딩 중 스켈레톤 UI를 사용할지,
    스피너를 사용할지 선호도가 있으신가요?"

Q2: "에러 발생 시 토스트 메시지로 처리할지,
    인라인 에러로 처리할지 결정해 주세요."
```

**3라운드 - 우려 사항**:
```
Q1: "외부 결제 API 장애 시 폴백 전략이 필요합니다.
    큐잉 후 재시도 vs 즉시 에러 반환 중 어떤 방식을 선호하시나요?"
```

**4라운드 - 트레이드오프**:
```
Q1: "초기 버전에서 오프라인 지원을 포함하면 복잡도가 증가합니다.
    MVP에서는 제외하고 나중에 추가하는 것이 어떨까요?"
```

## 출력 형식 예시

```markdown
# [프로젝트명] 스펙 문서 (인터뷰 완료)

## 기술적 결정사항
- 인증: JWT, 만료시간 24시간
- 상태관리: Context API 유지
- ...

## UI/UX 결정사항
- 로딩: 스켈레톤 UI 사용
- 에러: 인라인 에러 처리
- ...

## 식별된 우려 사항
- [ ] 결제 API 장애 대응: 큐잉 후 재시도 구현 필요
- ...

## 합의된 트레이드오프
- 오프라인 지원: MVP에서 제외, v2에서 추가
- ...
```

## 참조 파일

- 질문 템플릿: `.claude/skills/deep-interview/data/question-templates.md`
- 인터뷰어 에이전트: `.claude/agents/deep-interviewer.md`
