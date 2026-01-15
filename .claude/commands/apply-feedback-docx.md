# /apply-feedback-docx

승인된 피드백을 데이터 파일에 반영합니다.

## 사용법

```
/apply-feedback-docx <project-name>
```

## 인자

- `project-name`: 프로젝트명 (필수)

## 예시

```
/apply-feedback-docx N90WO1-PCT
/apply-feedback-docx WO2024123456
```

## 전제 조건

1. `/import-feedback-docx` 명령이 먼저 실행되어 있어야 합니다.
2. `feedback-review-report.md`에서 승인할 항목을 체크해야 합니다.

## 체크 방법

보고서에서 승인할 항목의 체크박스를 변경합니다:

```markdown
# 승인 전
- [ ] 승인 (ID: 1)

# 승인 후
- [x] 승인 (ID: 1)
```

## 워크플로우

```
feedback-review-report.md
    │
    ▼
[1] 승인된 항목 파싱
    - [x] 체크된 항목 추출
    │
    ▼
[2] 피드백 유형별 적용
    - terminology → terminology-db.md
    - error → error-patterns.md
    - style/other → feedback-log.md
    │
    ▼
[3] 번역 결과물에 직접 반영 ← NEW
    - translation-final.md 텍스트 교체
    - 백업 파일 자동 생성 (.md.backup)
    │
    ▼
[4] 결과 보고
    - 적용 건수 출력
    - 실패 항목 알림
```

## 대상 파일

| 피드백 유형 | 주요 대상 | 부가 대상 |
|-------------|-----------|-----------|
| **terminology** | terminology-db.md | project-tb.md |
| **error** | error-patterns.md | feedback-log.md |
| **style** | feedback-log.md | - |
| **other** | feedback-log.md | - |

## 출력 예시

```
=== 피드백 적용 완료 ===
적용 완료: 13건
  - 용어 추가: 3건
  - 용어 수정: 1건
  - 오류 패턴: 2건
  - 스타일 로그: 2건
  - 프로젝트 TB: 3건
  - 번역 결과물 수정: 5건
```

## 내부 스크립트

```bash
python .claude/skills/patent-translator/scripts/docx_feedback_cli.py apply <project-name>
```

## 롤백

변경 사항은 `feedback-log.md`에 타임스탬프와 함께 기록됩니다.
수동 롤백이 필요한 경우 로그를 참조하세요.

## 주의사항

- 이미 적용된 피드백을 다시 적용하면 중복 기록될 수 있습니다.
- 적용 전 Git 커밋을 권장합니다.

```bash
git add .claude/skills/patent-translator/data/
git commit -m "Before applying feedback from [project]"
```
