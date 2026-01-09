# /review-quality

번역 파일의 품질을 검토합니다.

## 사용법

```
/review-quality [file-path]
```

## 인자

- `file-path`: 검토할 번역 파일 경로 (필수)

## 예시

```
/review-quality output/project-001/sections/section-01-tac.md
/review-quality output/project-001/translation-final.md
```

## 검토 항목

| 항목 | 배점 | 검사 내용 |
|------|------|-----------|
| 정확성 | 50점 | 의미 왜곡, 누락, 오역, 첨가 |
| 용어 일관성 | 25점 | 상기 누락, TB 미준수 |
| 스타일 준수 | 15점 | 청구항 구조, 구두점 |
| 유창성 | 10점 | 비문, 어색한 표현 |

## 섹션별 가중치

- Claims: x1.5
- Abstract: x1.3
- Title: x1.2
- 기타: x1.0

## 출력

- 콘솔에 점수 및 오류 목록 출력
- `output/[project]/review-report-section-XX.md` 생성

## 95점 기준

- **95점 이상**: 통과
- **95점 미만**: 수정 필요 (구체적 수정 지시 제공)
