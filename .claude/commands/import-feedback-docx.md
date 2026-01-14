# /import-feedback-docx

검토된 Word 문서에서 Track Changes와 Comments를 추출하여 피드백 승인 보고서를 생성합니다.

## 사용법

```
/import-feedback-docx <docx-path> [project-name]
```

## 인자

- `docx-path`: 검토된 .docx 파일 경로 (필수)
- `project-name`: 프로젝트명 (선택, 기본값: 파일명에서 추출)

## 예시

```
/import-feedback-docx "G:\내 드라이브\Work2\patent-translator-agent\output\N90WO1-PCT\translation-final.docx"
/import-feedback-docx reviewed.docx WO2024123456
```

## 전제 조건

1. Word 문서에서 **Track Changes(변경 내용 추적)**가 활성화된 상태로 검토해야 합니다.
2. 변경 사항을 "승인" 또는 "거절"하지 않고 저장해야 합니다.
3. 코멘트(주석)도 함께 추출됩니다.

## 워크플로우

```
검토된 .docx
    │
    ▼
[1] Track Changes 추출
    - w:ins (삽입)
    - w:del (삭제)
    - Comments
    │
    ▼
[2] 피드백 자동 분류
    - terminology (용어 수정)
    - error (오류 수정)
    - style (스타일 개선)
    - other (기타)
    │
    ▼
[3] 승인 보고서 생성
    - feedback-review-report.md
```

## 출력 파일

| 파일 | 설명 |
|------|------|
| `feedback-extracted.json` | 추출된 원시 데이터 |
| `feedback-classified.json` | 분류된 피드백 데이터 |
| `feedback-review-report.md` | 체크박스 기반 승인 보고서 |

## 자동 분류 규칙

| 유형 | 분류 기준 | 대상 파일 |
|------|-----------|-----------|
| **terminology** | 용어 대체, 단어 수준 변경 | terminology-db.md, project-tb.md |
| **error** | 상기 누락, 참조부호 오류 | error-patterns.md |
| **style** | 표현 개선, 자연스러움 | feedback-log.md |
| **other** | 기타 피드백 | feedback-log.md |

## 다음 단계

1. 생성된 `feedback-review-report.md`를 열어 검토합니다.
2. 승인할 항목의 `[ ]`를 `[x]`로 변경합니다.
3. `/apply-feedback-docx` 명령을 실행하여 반영합니다.

```
/apply-feedback-docx [project-name]
```

## 내부 스크립트

```bash
python .claude/skills/patent-translator/scripts/docx_feedback_cli.py import <docx-path> --project <project-name>
```

## 요구사항

- Python 3.8+
- lxml 라이브러리 (`pip install lxml`)

## 제한사항

- **Track Changes가 꺼진 상태로 저장된 파일은 변경 사항을 추출할 수 없습니다.**
- 변경 사항을 "모두 승인" 또는 "모두 거절"한 후 저장하면 추출이 불가능합니다.
- 이미지나 표 내부의 변경 사항은 제한적으로 지원됩니다.
