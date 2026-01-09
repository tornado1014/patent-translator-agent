# /translate-section

특정 섹션만 번역합니다.

## 사용법

```
/translate-section [section-name]
```

## 인자

- `section-name`: 번역할 섹션 (필수)
  - `tac` 또는 `claims`: Title + Abstract + Claims
  - `background`: 배경기술
  - `summary`: 발명의 내용
  - `drawings`: 도면의 간단한 설명
  - `detailed`: 상세 설명

## 예시

```
/translate-section claims
/translate-section background
/translate-section detailed
```

## 워크플로우

1. Source Analyzer로 해당 섹션 분석
2. Patent Translator로 번역 수행
3. Translation Reviewer로 품질 검토 (95점 기준)
4. 통과 시 섹션 파일 저장

## 출력

- `output/[project]/sections/section-XX-[name].md`
- `output/[project]/project-tb.md` (업데이트)

## 주의사항

- 첫 번째 섹션(TAC)은 반드시 먼저 번역해야 함 (핵심 용어 확립)
- project-tb.md가 없으면 TAC 섹션부터 시작하도록 안내
