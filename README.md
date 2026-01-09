# Patent Translator Agent (영한 특허번역 에이전트)

Claude Code 기반 영한 특허번역 에이전트 시스템

## 특징

- **4개 에이전트 협업**: 분석 → 번역 → 검토 → 학습 루프
- **동적 TB(Term Base)**: 섹션별 번역 시 실시간 용어 누적
- **원문 오류 자동 검출**: 참조부호/용어 불일치 사전 검출
- **섹션별 번역**: 긴 문서(1만+ 단어)도 일관성 있게 처리
- **95점 품질 기준**: 특허의 법적 문서 특성 반영
- **워드 파일 자동 변환**: 바탕체 12pt, 양쪽정렬

## 에이전트 구성

| 에이전트 | 역할 |
|----------|------|
| Source Analyzer | 용어 추출, 도메인 식별, 원문 오류 검출 |
| Patent Translator | 스타일 가이드 기반 번역 수행 |
| Translation Reviewer | 품질 평가 (95점 미만 시 재번역) |
| Feedback Learner | 피드백 반영, 용어집/패턴 업데이트 |

## 사용법

### 1. Claude Code에서 저장소 열기
```bash
cd patent-translator-agent
claude
```

### 2. 번역 시작
```
특허 번역해줘
```
또는
```
/patent-translator
```

### 3. 원문 파일 제공
프롬프트에 따라 원문 파일 경로를 제공합니다.

### 4. 피드백 제공 (선택)
```
"substrate"는 화학 분야니까 "기재"로 번역해줘
```

## 모바일 사용

Claude 모바일 앱에서 이 GitHub 저장소를 연결하면 동일하게 사용 가능합니다.

1. Claude 모바일 앱 실행
2. 설정 > GitHub 연결
3. 이 저장소 선택
4. "특허 번역해줘" 입력

## 파일 구조

```
patent-translator-agent/
├── .claude/
│   ├── agents/
│   │   ├── source-analyzer.md      # 원문 분석 에이전트
│   │   ├── patent-translator.md    # 번역 에이전트
│   │   ├── translation-reviewer.md # 검토 에이전트
│   │   └── feedback-learner.md     # 피드백 학습 에이전트
│   └── skills/
│       └── patent-translator/
│           ├── SKILL.md            # 스킬 오케스트레이터
│           ├── data/
│           │   ├── style-guide.md        # 스타일 가이드
│           │   ├── terminology-db.md     # 기본 용어집
│           │   ├── error-patterns.md     # 번역 오류 패턴
│           │   ├── source-error-patterns.md  # 원문 오류 패턴
│           │   └── feedback-log.md       # 피드백 로그
│           ├── templates/
│           │   └── patent-template.docx  # 워드 템플릿
│           └── scripts/
│               └── convert-to-docx.py    # 워드 변환 스크립트
├── output/                         # 번역 결과 (로컬 전용, .gitignore)
├── .gitignore
├── README.md
└── CLAUDE.md
```

## 번역 워크플로우

```
원문 입력
    ↓
[Source Analyzer] 용어 추출 + 원문 오류 검출
    ↓
[Patent Translator] 섹션별 번역
    ↓
[Translation Reviewer] 품질 검토 (95점↑ 통과)
    ↓
[Feedback Learner] 피드백 반영
    ↓
파일 통합 → 워드 변환
```

## 섹션별 번역 순서

1. **Title + Abstract + Claims**: 핵심 용어 확립 (한 번에 처리)
2. **Background**: 배경기술
3. **Summary**: 발명의 내용
4. **Drawings**: 도면의 간단한 설명
5. **Detailed Description**: 상세 설명 (5,000단어 단위 분할)

## 출력 파일

| 파일 | 설명 |
|------|------|
| `project-tb.md` | 동적 Term Base (실시간 누적) |
| `source-error-report.md` | 원문 오류 보고서 |
| `translation-final.md` | 통합 번역문 (마크다운) |
| `translation-final.docx` | 최종 워드 파일 |

## 요구사항

- Claude Code (CLI)
- Python 3.8+ (워드 변환용)
- python-docx 패키지

```bash
pip install python-docx
```

## 학습 데이터

피드백을 제공하면 다음 파일들이 자동 업데이트됩니다:

- `terminology-db.md`: 용어집 확장
- `error-patterns.md`: 오류 패턴 누적
- `feedback-log.md`: 피드백 이력

이 데이터는 GitHub에 커밋되어 다음 번역에 활용됩니다.

## 라이선스

Private - Personal Use Only
