# /export-docx

번역 결과를 Word 문서로 변환합니다.

## 사용법

```
/export-docx [project-name]
/export-docx [project-name] --sections-only
```

## 인자

- `project-name`: 프로젝트명 (필수)
- `--sections-only`: 섹션 파일만 병합 (최종 검토 없이)

## 예시

```
/export-docx project-001
/export-docx WO2024123456 --sections-only
```

## 워크플로우

1. `output/[project]/sections/` 내 모든 섹션 파일 수집
2. 섹션 순서대로 병합 → `translation-final.md`
3. Word 변환 → `translation-final.docx`

## 변환 설정

| 항목 | 값 |
|------|-----|
| 폰트 | 바탕체 (Batang) |
| 폰트 크기 | 12pt |
| 문단 정렬 | 양쪽 정렬 (Justify) |
| 줄 간격 | 1.5줄 |

## 출력

- `output/[project]/translation-final.md` - 통합 마크다운
- `output/[project]/translation-final.docx` - 최종 Word 파일

## 변환 스크립트

내부적으로 `scripts/convert-to-docx.py` 사용

```bash
python scripts/convert-to-docx.py output/[project]/translation-final.md
```

## 요구사항

- Python 3.x
- python-docx 라이브러리 (`pip install python-docx`)
