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

---

## TOKEN LIMIT GUARD

> **중요**: Claude는 translation-final.md 파일을 **직접 읽거나 생성하지 않습니다**.
> 모든 병합/변환 작업은 Python 스크립트로 수행합니다.

### 금지 행위

- 모든 섹션 파일을 Read로 읽어서 Write로 병합
- translation-final.md 전체 내용 읽기
- 병합 결과를 직접 확인하기 위해 파일 열기

### 허용 행위

- Python 스크립트 실행 (Bash 도구)
- 스크립트 출력의 메타데이터 확인

---

## 워크플로우

### Step 1: 섹션 폴더 확인

```bash
ls output/[project]/sections/
```

섹션 파일 존재 여부 확인

### Step 2: 섹션 병합 (Python)

```bash
python .claude/skills/patent-translator/scripts/merge-sections.py output/[project] --json
```

**출력 예시** (JSON):
```json
{
  "status": "success",
  "sections_merged": 6,
  "total_lines": 310,
  "total_bytes": 76234,
  "hash": "sha256:abc123..."
}
```

### Step 3: 병합 검증 (Python)

```bash
python .claude/skills/patent-translator/scripts/verify-merge.py output/[project]/translation-final.md
```

**출력 예시**:
```
[MERGE_VERIFIED:OK] output/project/translation-final.md
  라인 수: 310
  파일 크기: 76,234 bytes
  섹션 수: 6

  섹션 존재 여부:
    [O] claims: line 1
    [O] detailed: line 95
```

### Step 4: Word 변환 (Python)

```bash
python .claude/skills/patent-translator/scripts/convert-to-docx.py output/[project]/translation-final.md
```

---

## 사용자 보고

병합 완료 후 Claude가 사용자에게 보고하는 내용:

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

## 변환 설정

| 항목 | 값 |
|------|-----|
| 폰트 | 바탕체 (Batang) |
| 폰트 크기 | 12pt |
| 문단 정렬 | 양쪽 정렬 (Justify) |
| 줄 간격 | 1.5줄 |

---

## 출력

- `output/[project]/translation-final.md` - 통합 마크다운
- `output/[project]/translation-final.docx` - 최종 Word 파일

---

## 요구사항

- Python 3.x
- python-docx 라이브러리 (`pip install python-docx`)

---

## 스크립트 경로

| 스크립트 | 경로 | 용도 |
|----------|------|------|
| merge-sections.py | `scripts/merge-sections.py` | 섹션 병합 + 메타데이터 출력 |
| verify-merge.py | `scripts/verify-merge.py` | 병합 파일 검증 |
| convert-to-docx.py | `scripts/convert-to-docx.py` | Word 변환 |
