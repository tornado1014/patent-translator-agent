# 번역 예시 (Input/Output)

> 이 파일은 SKILL.md에서 참조됩니다.

---

## 예시 1: 청구항 번역 (Method Claim)

**입력 (영문)**:
```text
1. A method of treating cancer in a patient in need thereof, comprising
administering to the patient a therapeutically effective amount of a compound
of Formula (I), wherein the compound is substantially amorphous.
```

**출력 (한국어)**:
```text
1. 암 치료를 필요로 하는 환자에서 암을 치료하는 방법으로서,
화학식 (I)의 화합물의 치료적 유효량을 상기 환자에게 투여하는 단계를 포함하고,
여기서 상기 화합물은 실질적으로 비정질인, 방법.
```

**처리 포인트**:
- `a patient` → `환자` (첫 등장, 부정형)
- `the patient` → `상기 환자` (재등장, 상기 삽입)
- `a compound` → `화합물` (첫 등장)
- `the compound` → `상기 화합물` (재등장)
- `comprising` → `포함하고` (개방형 전환구)

---

## 예시 2: 청구항 번역 (Composition Claim)

**입력 (영문)**:
```text
5. A pharmaceutical composition comprising:
(a) an antibody drug conjugate (ADC); and
(b) a pharmaceutically acceptable carrier,
wherein the ADC comprises a humanized antibody conjugated to a cytotoxic agent.
```

**출력 (한국어)**:
```text
5. 하기를 포함하는 약학적 조성물:
(a) 항체-약물 접합체 (ADC); 및
(b) 약학적으로 허용가능한 담체,
여기서 상기 ADC는 세포독성제에 접합된 인간화 항체를 포함한다.
```

**처리 포인트**:
- `antibody drug conjugate (ADC)` → `항체-약물 접합체 (ADC)` (약어 병기)
- `the ADC` → `상기 ADC` (재등장)
- `humanized antibody` → `인간화 항체` (전문 용어)
- 리스트 구조 `(a)`, `(b)` 유지

---

## 예시 3: 원문 오류 처리

**입력 (영문 - 오류 포함)**:
```text
[0045] The housing (10) is connected to the base (20).
[0067] The casing (10) provides structural support.
```

**Source Analyzer 출력** (`source-error-report.md`):
```markdown
## 참조부호 불일치 (Major)
| 위치 | 참조부호 | 문제 |
|------|----------|------|
| [0045] | 10 | "housing"으로 기술 |
| [0067] | 10 | "casing"으로 기술 → 통일 필요 |
```

**번역 출력** (주석 포함):
```text
[0045] 상기 하우징(10)은 베이스(20)에 연결된다.
[0067] 상기 케이싱(10) [원문 오류 - Major: [0045]에서 "housing"으로도 기술됨] 은
구조적 지지를 제공한다.
```

---

## 예시 4: 동적 TB 업데이트

**섹션 1 (Claims) 번역 후 project-tb.md**:
```markdown
## 핵심 용어 (Title/Abstract/Claims에서 확립)
| English | Korean | 첫 등장 | 비고 |
|---------|--------|---------|------|
| antibody drug conjugate | 항체-약물 접합체 | Claim 5 | ADC |
| humanized antibody | 인간화 항체 | Claim 5 | |
| therapeutically effective amount | 치료적 유효량 | Claim 1 | |
```

**섹션 2 (Background) 번역 후 추가**:
```markdown
## 배경기술 추가 용어 (섹션 2)
| English | Korean | 첫 등장 | 비고 |
|---------|--------|---------|------|
| prior art | 선행 기술 | [0003] | |
| conventional therapy | 종래 치료법 | [0005] | |
```

> **참고**: 동일 용어(예: `antibody drug conjugate`)가 섹션 2에서 다시 나타나면 TB에 추가하지 않고 기존 번역(`항체-약물 접합체`)을 그대로 사용합니다.
