#!/usr/bin/env python3
"""
영한 특허번역 기계적 검토 스크립트

사용법:
    python validate-translation.py <section_file.md> [source_file.txt]

기능:
    - 참조부호 일치/형식 검사
    - 청구항 구조 검사
    - 약어 형식 검사
    - 서수 형식 검사
    - 전환구 일관성 검사
    - 기본 상기 검사
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple


class TranslationValidator:
    def __init__(self, target_path: str, source_path: str = None):
        self.target_path = Path(target_path)
        self.target_text = self.target_path.read_text(encoding='utf-8')

        # 프로젝트 디렉토리 찾기 (sections/ 상위)
        self.project_dir = self._find_project_dir()

        # 원문 파일이 있으면 로드
        self.source_text = None
        if source_path:
            source_file = Path(source_path)
            if source_file.exists():
                self.source_text = source_file.read_text(encoding='utf-8')

        # 동적 컨텍스트 데이터 로드
        self.context_data = self._load_context_data()

        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []

    def _find_project_dir(self) -> Path:
        """프로젝트 디렉토리 찾기 (sections/ 상위 또는 output/[project]/)"""
        current = self.target_path.parent
        if current.name == 'sections':
            return current.parent
        # output/[project]/ 패턴 찾기
        for parent in self.target_path.parents:
            if parent.parent.name == 'output':
                return parent
        return current

    def _load_context_data(self) -> Dict:
        """chunk-context.md와 project-tb.md에서 동적 데이터 로드"""
        data = {'key_nouns': [], 'reference_map': {}}

        # chunk-context.md에서 핵심 명사 로드
        chunk_context = self.project_dir / 'chunk-context.md'
        if chunk_context.exists():
            content = chunk_context.read_text(encoding='utf-8')
            # "## 핵심 명사 상기 상태" 섹션 파싱
            noun_section = re.search(r'## 핵심 명사.*?\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
            if noun_section:
                for line in noun_section.group(1).split('\n'):
                    # 테이블 행 파싱: | 명사 | 첫 등장 | 상기 필요 |
                    match = re.match(r'\|\s*([^|]+)\s*\|', line)
                    if match and match.group(1).strip() not in ['명사', '---', '']:
                        data['key_nouns'].append(match.group(1).strip())

        # project-tb.md에서 핵심 용어 추가 로드
        project_tb = self.project_dir / 'project-tb.md'
        if project_tb.exists():
            content = project_tb.read_text(encoding='utf-8')
            # Korean 열에서 용어 추출
            for line in content.split('\n'):
                match = re.match(r'\|[^|]+\|\s*([가-힣\s]+)\s*\|', line)
                if match and match.group(1).strip() not in ['Korean', '---', '']:
                    term = match.group(1).strip()
                    if len(term) >= 2 and term not in data['key_nouns']:
                        data['key_nouns'].append(term)

        return data

    def add_error(self, check_type: str, message: str, location: str = None):
        self.errors.append({
            'type': check_type,
            'message': message,
            'location': location or 'N/A'
        })

    def add_warning(self, check_type: str, message: str, location: str = None):
        self.warnings.append({
            'type': check_type,
            'message': message,
            'location': location or 'N/A'
        })

    def check_reference_format(self) -> bool:
        """참조부호 형식 검사: 명사(10) vs 명사 (10)"""
        # 공백 + 괄호 + 숫자 패턴 찾기 (잘못된 형식)
        bad_pattern = re.compile(r'[가-힣a-zA-Z]\s+\(\d+[a-zA-Z]?\)')

        for i, line in enumerate(self.target_text.split('\n'), 1):
            matches = bad_pattern.findall(line)
            for match in matches:
                self.add_error(
                    'reference_format',
                    f'참조부호 형식 오류: "{match}" → 공백 제거 필요',
                    f'Line {i}'
                )

        return len([e for e in self.errors if e['type'] == 'reference_format']) == 0

    def check_claim_structure(self) -> bool:
        """청구항 구조 검사"""
        # 청구항 패턴 찾기
        claim_pattern = re.compile(r'\[청구항\s*(\d+)\]')
        claims = claim_pattern.findall(self.target_text)

        if not claims:
            return True  # 청구항이 없으면 검사 스킵

        # 청구항 번호 연속성 검사
        claim_numbers = [int(c) for c in claims]
        expected = list(range(1, max(claim_numbers) + 1))
        missing = set(expected) - set(claim_numbers)

        if missing:
            self.add_error(
                'claim_structure',
                f'청구항 번호 누락: {sorted(missing)}',
                'Claims section'
            )

        # 각 청구항이 마침표로 끝나는지 검사
        claim_blocks = re.split(r'\[청구항\s*\d+\]', self.target_text)
        for i, block in enumerate(claim_blocks[1:], 1):
            next_claim = re.search(r'\[청구항\s*\d+\]', block)
            if next_claim:
                block = block[:next_claim.start()]

            block = block.strip()
            if block and not block.rstrip().endswith('.'):
                last_word = block.split()[-1] if block.split() else ''
                if last_word not in ['시스템.', '방법.', '매체.']:
                    self.add_warning(
                        'claim_structure',
                        f'청구항 {i}: 마침표로 종결되지 않음',
                        f'Claim {i}'
                    )

        return len([e for e in self.errors if e['type'] == 'claim_structure']) == 0

    def check_ordinal_format(self) -> bool:
        """서수 형식 검사: 제1, 제2 vs 첫째, 둘째"""
        bad_ordinals = ['첫째', '둘째', '셋째', '넷째', '다섯째', '첫번째', '두번째', '세번째']

        for i, line in enumerate(self.target_text.split('\n'), 1):
            for ordinal in bad_ordinals:
                if ordinal in line:
                    self.add_warning(
                        'ordinal_format',
                        f'서수 형식: "{ordinal}" → "제N" 형식 권장',
                        f'Line {i}'
                    )

        return len([e for e in self.errors if e['type'] == 'ordinal_format']) == 0

    def check_transitional_phrases(self) -> bool:
        """전환구 일관성 검사"""
        if self.source_text:
            if 'comprising' in self.source_text.lower():
                if '구성되는' in self.target_text and '포함하는' not in self.target_text:
                    self.add_warning(
                        'transitional_phrase',
                        'comprising → "포함하는" 권장 (구성되는 = consisting of)',
                        'General'
                    )

            if 'consisting of' in self.source_text.lower():
                if '이루어지는' not in self.target_text and '구성되는' not in self.target_text:
                    self.add_warning(
                        'transitional_phrase',
                        'consisting of → "이루어지는/구성되는" 필요 (closed-ended)',
                        'General'
                    )

        return True

    def check_reference_completeness(self) -> bool:
        """원문-번역문 참조부호 일치 검사"""
        if not self.source_text:
            return True  # 원문 없으면 검사 스킵

        # 원문과 번역문에서 참조부호 추출
        source_refs = set(re.findall(r'\((\d+[a-zA-Z]?)\)', self.source_text))
        target_refs = set(re.findall(r'\((\d+[a-zA-Z]?)\)', self.target_text))

        # 누락된 참조부호
        missing = source_refs - target_refs
        if missing:
            self.add_error(
                'reference_completeness',
                f'번역문에 누락된 참조부호: {sorted(missing, key=lambda x: int(re.match(r"\d+", x).group()))}',
                'General'
            )

        # 원문에 없는 참조부호 (경고)
        extra = target_refs - source_refs
        if extra:
            self.add_warning(
                'reference_completeness',
                f'원문에 없는 참조부호 (확인 필요): {sorted(extra, key=lambda x: int(re.match(r"\d+", x).group()))}',
                'General'
            )

        return len(missing) == 0

    def check_sanggi_basic(self) -> bool:
        """기본 상기 검사 (동적 데이터 기반)"""
        # 동적으로 로드된 핵심 명사 사용, 없으면 기본값
        key_nouns = self.context_data.get('key_nouns', [])
        if not key_nouns:
            # 폴백: 일반적인 특허 용어
            key_nouns = ['장치', '시스템', '방법', '구성요소', '모듈']

        for noun in key_nouns:
            first_match = re.search(rf'(?<!상기\s){re.escape(noun)}', self.target_text)
            if first_match:
                after_first = self.target_text[first_match.end():]
                bare_matches = re.findall(rf'(?<!상기\s)(?<!상기){re.escape(noun)}', after_first)
                sanggi_matches = re.findall(rf'상기\s*{re.escape(noun)}', after_first)

                if bare_matches and len(bare_matches) > len(sanggi_matches):
                    self.add_warning(
                        'sanggi_check',
                        f'"{noun}": 재등장 시 "상기" 누락 가능성 ({len(bare_matches)}건)',
                        'General'
                    )

        return True

    def check_abbreviation_format(self) -> bool:
        """약어 형식 검사"""
        abbr_pattern = re.compile(r'\b([A-Z]{2,5})\b')
        abbrs_in_text = set(abbr_pattern.findall(self.target_text))

        for abbr in abbrs_in_text:
            if abbr in ['RAID', 'LUN', 'SSD', 'RG', 'RU', 'FDP', 'ECC']:
                definition_pattern = re.compile(
                    rf'[가-힣\s]+[\(\[][^)]*{abbr}[^\]]*[\)\]]|'
                    rf'{abbr}[\(\[][^)]*[가-힣][^\]]*[\)\]]'
                )
                if not definition_pattern.search(self.target_text):
                    first_occurrence = self.target_text.find(abbr)
                    context = self.target_text[max(0, first_occurrence-50):first_occurrence+50]
                    if f'({abbr})' not in context and f'[{abbr}]' not in context:
                        if f', {abbr}' not in context:
                            self.add_warning(
                                'abbreviation_format',
                                f'약어 "{abbr}": 첫 등장 시 풀이 형식 확인 필요',
                                'General'
                            )

        return True

    def check_number_unit_spacing(self) -> bool:
        """숫자-단위 공백 검사"""
        units = ['mL', 'mg', 'kg', 'mm', 'cm', 'nm', 'μm', 'kHz', 'MHz', 'GHz']

        for unit in units:
            pattern = re.compile(rf'\d{re.escape(unit)}')
            for i, line in enumerate(self.target_text.split('\n'), 1):
                if pattern.search(line):
                    self.add_warning(
                        'number_unit_spacing',
                        f'숫자와 단위({unit}) 사이 공백 필요',
                        f'Line {i}'
                    )

        return True

    def validate_all(self) -> Tuple[bool, str]:
        """모든 검사 실행"""
        self.check_reference_format()
        self.check_reference_completeness()  # 참조부호 완전성 검사 추가
        self.check_claim_structure()
        self.check_ordinal_format()
        self.check_transitional_phrases()
        self.check_sanggi_basic()
        self.check_abbreviation_format()
        self.check_number_unit_spacing()

        return self.generate_report()

    def generate_report(self) -> Tuple[bool, str]:
        """검증 보고서 생성"""
        lines = []

        if self.errors:
            lines.append('[MECHANICAL_CHECK_FAILED] 기계적 검토 오류 발견')
            lines.append('')
            lines.append('## 오류 (수정 필요)')
            for err in self.errors:
                lines.append(f"  - [{err['type']}] {err['message']} ({err['location']})")

        if self.warnings:
            if not self.errors:
                lines.append('[MECHANICAL_CHECK_PASSED] 기계적 검토 통과 (경고 있음)')
            lines.append('')
            lines.append('## 경고 (검토 권장)')
            for warn in self.warnings:
                lines.append(f"  - [{warn['type']}] {warn['message']} ({warn['location']})")

        if not self.errors and not self.warnings:
            lines.append('[MECHANICAL_CHECK_PASSED] 기계적 검토 통과')

        passed = len(self.errors) == 0
        return passed, '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target_path = sys.argv[1]
    source_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(target_path).exists():
        print(f"Error: 파일을 찾을 수 없습니다: {target_path}")
        sys.exit(1)

    validator = TranslationValidator(target_path, source_path)
    passed, report = validator.validate_all()

    print(report)
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
