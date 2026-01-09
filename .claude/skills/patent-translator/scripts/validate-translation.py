#!/usr/bin/env python3
"""
번역 품질 검증 스크립트

사용법:
    python validate-translation.py <translation-file> [--tb <project-tb-file>]

예시:
    python validate-translation.py output/project-001/sections/section-01-tac.md
    python validate-translation.py output/project-001/sections/section-01-tac.md --tb output/project-001/project-tb.md
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class ValidationError:
    """검증 오류"""
    severity: str  # Critical, Major, Minor
    category: str  # accuracy, terminology, style, fluency
    line: int
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """검증 결과"""
    file_path: str
    total_score: float = 100.0
    errors: List[ValidationError] = field(default_factory=list)

    # 항목별 점수
    accuracy_score: float = 50.0
    terminology_score: float = 25.0
    style_score: float = 15.0
    fluency_score: float = 10.0

    def add_error(self, error: ValidationError):
        self.errors.append(error)

        # 감점 적용
        deduction = self._get_deduction(error)

        if error.category == "accuracy":
            self.accuracy_score = max(0, self.accuracy_score - deduction)
        elif error.category == "terminology":
            self.terminology_score = max(0, self.terminology_score - deduction)
        elif error.category == "style":
            self.style_score = max(0, self.style_score - deduction)
        elif error.category == "fluency":
            self.fluency_score = max(0, self.fluency_score - deduction)

        self._recalculate_total()

    def _get_deduction(self, error: ValidationError) -> float:
        """심각도별 감점"""
        deductions = {
            "Critical": {"accuracy": 15, "terminology": 10, "style": 8, "fluency": 5},
            "Major": {"accuracy": 8, "terminology": 5, "style": 3, "fluency": 3},
            "Minor": {"accuracy": 3, "terminology": 2, "style": 1, "fluency": 1},
        }
        return deductions.get(error.severity, {}).get(error.category, 0)

    def _recalculate_total(self):
        self.total_score = (
            self.accuracy_score +
            self.terminology_score +
            self.style_score +
            self.fluency_score
        )

    def is_passed(self) -> bool:
        return self.total_score >= 95.0


class TranslationValidator:
    """번역 검증기"""

    def __init__(self, tb_path: Optional[str] = None):
        self.tb_terms = {}
        if tb_path:
            self._load_tb(tb_path)

    def _load_tb(self, tb_path: str):
        """project-tb.md 로드"""
        try:
            with open(tb_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 테이블에서 용어 추출 (| English | Korean | 형식)
            pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
            for match in re.finditer(pattern, content):
                eng = match.group(1).strip()
                kor = match.group(2).strip()
                if eng and kor and eng != "English" and eng != "---":
                    self.tb_terms[eng.lower()] = kor
        except Exception as e:
            print(f"Warning: TB 로드 실패 - {e}", file=sys.stderr)

    def validate(self, file_path: str) -> ValidationResult:
        """번역 파일 검증"""
        result = ValidationResult(file_path=file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            result.add_error(ValidationError(
                severity="Critical",
                category="accuracy",
                line=0,
                message=f"파일 읽기 실패: {e}"
            ))
            return result

        content = ''.join(lines)

        # 1. 상기(Antecedent Basis) 검사
        self._check_antecedent_basis(lines, result)

        # 2. 용어 일관성 검사
        self._check_terminology_consistency(content, result)

        # 3. 스타일 검사
        self._check_style(lines, result)

        # 4. 유창성 검사
        self._check_fluency(lines, result)

        return result

    def _check_antecedent_basis(self, lines: List[str], result: ValidationResult):
        """상기 누락 검사"""
        # 첫 등장한 명사 추적
        first_mentions = set()

        # 상기가 붙어야 하는 패턴 (재등장)
        sanggi_pattern = re.compile(r'상기\s+(\S+)')
        noun_pattern = re.compile(r'(?:상기\s+)?(\S+(?:물|체|제|기|판|부|층|막|액))')

        for i, line in enumerate(lines, 1):
            # 상기가 있는 명사 찾기
            sanggi_matches = sanggi_pattern.findall(line)
            for noun in sanggi_matches:
                if noun not in first_mentions:
                    # 첫 등장인데 상기가 붙어있음 - 오류
                    result.add_error(ValidationError(
                        severity="Major",
                        category="terminology",
                        line=i,
                        message=f"첫 등장 명사에 '상기' 사용: '{noun}'",
                        suggestion=f"'{noun}'의 첫 등장 시 '상기' 제거"
                    ))
                first_mentions.add(noun)

            # 상기 없는 명사 찾기 (재등장 시 오류)
            all_nouns = noun_pattern.findall(line)
            for noun in all_nouns:
                clean_noun = noun.replace("상기 ", "").strip()
                if clean_noun in first_mentions and f"상기 {clean_noun}" not in line:
                    # 재등장인데 상기가 없음 - 청구항에서는 Critical
                    if "청구항" in ''.join(lines[:10]) or "claim" in ''.join(lines[:10]).lower():
                        severity = "Critical"
                    else:
                        severity = "Major"

                    # 같은 줄에 상기+명사가 있으면 skip
                    if re.search(rf'상기\s+{re.escape(clean_noun)}', line):
                        continue

                first_mentions.add(clean_noun)

    def _check_terminology_consistency(self, content: str, result: ValidationResult):
        """용어 일관성 검사"""
        if not self.tb_terms:
            return

        # TB에 있는 용어의 다른 번역 사용 여부 확인
        # (간략화된 검사 - 실제로는 더 정교한 로직 필요)
        pass

    def _check_style(self, lines: List[str], result: ValidationResult):
        """스타일 검사"""
        for i, line in enumerate(lines, 1):
            # 참조부호 형식 검사: 핸드가드 (12) → 핸드가드(12)
            if re.search(r'\S\s+\(\d+\)', line):
                result.add_error(ValidationError(
                    severity="Minor",
                    category="style",
                    line=i,
                    message="참조부호 앞 불필요한 공백",
                    suggestion="참조부호는 명사에 직접 붙임 (예: 하우징(10))"
                ))

            # 서수 형식 검사: 첫째/둘째 → 제1/제2
            if re.search(r'첫째|둘째|셋째|넷째', line):
                result.add_error(ValidationError(
                    severity="Minor",
                    category="style",
                    line=i,
                    message="서수 형식 오류",
                    suggestion="서수는 '제1, 제2, 제3' 형식 사용"
                ))

            # SI 단위 공백 검사: 10mL → 10 mL
            if re.search(r'\d+(?:mL|mg|kg|mm|cm|nm|μm|Hz|kHz|MHz)', line):
                result.add_error(ValidationError(
                    severity="Minor",
                    category="style",
                    line=i,
                    message="SI 단위 앞 공백 누락",
                    suggestion="숫자와 단위 사이에 공백 (예: 10 mL)"
                ))

    def _check_fluency(self, lines: List[str], result: ValidationResult):
        """유창성 검사"""
        for i, line in enumerate(lines, 1):
            # 번역투 패턴 검사
            if re.search(r'~에 의해\s+~되', line):
                result.add_error(ValidationError(
                    severity="Minor",
                    category="fluency",
                    line=i,
                    message="번역투 표현",
                    suggestion="능동태로 변환 권장"
                ))


def print_result(result: ValidationResult):
    """결과 출력"""
    print("=" * 60)
    print(f"번역 검증 결과: {result.file_path}")
    print("=" * 60)

    print(f"\n총점: {result.total_score:.1f}/100")
    print(f"  - 정확성: {result.accuracy_score:.1f}/50")
    print(f"  - 용어 일관성: {result.terminology_score:.1f}/25")
    print(f"  - 스타일 준수: {result.style_score:.1f}/15")
    print(f"  - 유창성: {result.fluency_score:.1f}/10")

    print(f"\n결과: {'✅ 통과 (95점 이상)' if result.is_passed() else '❌ 수정 필요 (95점 미만)'}")

    if result.errors:
        print(f"\n검출된 오류 ({len(result.errors)}건):")
        print("-" * 60)

        for err in result.errors:
            print(f"[{err.severity}] Line {err.line}: {err.message}")
            if err.suggestion:
                print(f"    → {err.suggestion}")

        print("-" * 60)

    return 0 if result.is_passed() else 1


def main():
    parser = argparse.ArgumentParser(description="번역 품질 검증")
    parser.add_argument("file", help="검증할 번역 파일")
    parser.add_argument("--tb", help="project-tb.md 파일 경로")

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: 파일을 찾을 수 없음 - {args.file}", file=sys.stderr)
        return 1

    validator = TranslationValidator(args.tb)
    result = validator.validate(args.file)

    return print_result(result)


if __name__ == "__main__":
    sys.exit(main())
