# /update-tb

용어집(Term Base)을 업데이트합니다.

## 사용법

```
/update-tb [term] [translation]
/update-tb [term] [translation] --domain [domain]
/update-tb --file [csv-file]
```

## 인자

- `term`: 영문 용어 (필수)
- `translation`: 한국어 번역 (필수)
- `--domain`: 도메인 지정 (선택, 예: pharma, semiconductor, mechanical)
- `--file`: CSV 파일로 일괄 업데이트 (선택)

## 예시

```
/update-tb "substrate" "기재" --domain pharma
/update-tb "antibody drug conjugate" "항체-약물 접합체"
/update-tb --file new-terms.csv
```

## CSV 형식

```csv
English,Korean,Domain,Note
substrate,기재,pharma,화학 분야
housing,하우징,mechanical,
```

## 업데이트 대상

1. **terminology-db.md**: 기본 용어집 (영구 저장)
2. **project-tb.md**: 프로젝트별 용어집 (현재 프로젝트만)

## 충돌 처리

- 기존 용어와 다른 번역 시 확인 요청
- `--force` 옵션으로 강제 덮어쓰기 가능

## 학습 연동

- Feedback Learner가 자동으로 feedback-log.md에 기록
- 동일 피드백 2회 이상 시 error-patterns.md에 패턴 등록
