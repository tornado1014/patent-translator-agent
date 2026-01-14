#!/usr/bin/env python3
"""
병합 파일 검증 스크립트

이 스크립트는 병합된 translation-final.md 파일의 무결성을 검증합니다.
Claude가 전체 파일 내용을 읽지 않고도 병합 결과를 확인할 수 있습니다.

사용법:
    python verify-merge.py <merged_file> [--expected-sections N] [--json]

예시:
    python verify-merge.py output/N90WO1-PCT/translation-final.md
    python verify-merge.py output/N90WO1-PCT/translation-final.md --expected-sections 6

출력:
    - 검증 결과 리포트 (메타데이터만, 파일 내용 없음)

주의:
    이 스크립트는 파일 내용을 stdout에 출력하지 않습니다.
    Claude는 이 검증 결과만 확인합니다.
"""

import sys
import os
import re
import json
import hashlib
import argparse
from pathlib import Path


def verify_merge(merged_file: Path, expected_sections: int = None) -> dict:
    """
    병합 파일 검증

    Args:
        merged_file: 검증할 병합 파일 경로
        expected_sections: 예상 섹션 수 (선택)

    Returns:
        dict: 검증 결과
            - status: "success", "warning", "error"
            - file: 파일 경로
            - lines: 라인 수
            - bytes: 바이트 수
            - hash: SHA256 해시
            - sections_detected: 감지된 섹션 수
            - sections_found: 주요 섹션 존재 여부
            - warnings: 경고 목록 (있을 경우)
    """

    if not merged_file.exists():
        return {
            "status": "error",
            "message": f"파일을 찾을 수 없습니다: {merged_file}"
        }

    # 파일 읽기
    try:
        content = merged_file.read_text(encoding='utf-8')
    except Exception as e:
        return {
            "status": "error",
            "message": f"파일 읽기 오류: {e}"
        }

    lines = content.split('\n')

    # 빈 파일 체크
    if len(content.strip()) == 0:
        return {
            "status": "error",
            "message": "빈 파일입니다"
        }

    # 기본 메타데이터
    result = {
        "status": "success",
        "file": str(merged_file),
        "lines": len(lines),
        "bytes": len(content.encode('utf-8')),
        "hash": f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}",
        "warnings": []
    }

    # 섹션 구분자 (---) 카운트로 섹션 수 추정
    # 병합 시 '\n\n---\n\n'로 연결하므로
    separator_count = len(re.findall(r'\n---\n', content))
    result["sections_detected"] = separator_count + 1

    # 예상 섹션 수 검증
    if expected_sections:
        if result["sections_detected"] != expected_sections:
            result["warnings"].append(
                f"섹션 수 불일치: 예상 {expected_sections}, 실제 {result['sections_detected']}"
            )

    # 주요 섹션 마커 존재 확인
    # 특허 문서의 주요 섹션들
    section_markers = {
        "title": ["【발명의 명칭】", "발명의 명칭", "Title"],
        "abstract": ["【요약서】", "【요약】", "요약"],
        "claims": ["【청구범위】", "【청구항", "청구항 1"],
        "background": ["【배경기술】", "배경기술", "기술분야"],
        "drawings": ["【도면의 간단한 설명】", "도면", "도 1"],
        "detailed": ["【발명을 실시하기 위한 구체적인 내용】", "상세한 설명", "실시예"]
    }

    result["sections_found"] = {}

    for section_name, markers in section_markers.items():
        found = False
        location = None

        for marker in markers:
            if marker in content:
                found = True
                # 위치 찾기 (라인 번호)
                for i, line in enumerate(lines, 1):
                    if marker in line:
                        location = f"line {i}"
                        break
                break

        if found:
            result["sections_found"][section_name] = location
        else:
            result["sections_found"][section_name] = "not found"

    # 필수 섹션 누락 경고
    required_sections = ["claims", "detailed"]
    for section in required_sections:
        if result["sections_found"].get(section) == "not found":
            result["warnings"].append(f"필수 섹션 누락: {section}")

    # 최종 상태 결정
    if result["warnings"]:
        result["status"] = "warning"

    return result


def format_report(result: dict) -> str:
    """결과를 사람이 읽기 쉬운 형식으로 포맷"""

    if result["status"] == "error":
        return f"[VERIFY_FAILED] {result.get('message', 'Unknown error')}"

    status_icon = "OK" if result["status"] == "success" else "WARNING"

    lines = [
        f"[MERGE_VERIFIED:{status_icon}] {result['file']}",
        f"  라인 수: {result['lines']:,}",
        f"  파일 크기: {result['bytes']:,} bytes",
        f"  섹션 수: {result['sections_detected']}",
        f"  해시: {result['hash']}",
        "",
        "  섹션 존재 여부:"
    ]

    for section, location in result["sections_found"].items():
        icon = "O" if location != "not found" else "X"
        lines.append(f"    [{icon}] {section}: {location}")

    if result["warnings"]:
        lines.append("")
        lines.append("  경고:")
        for warning in result["warnings"]:
            lines.append(f"    ! {warning}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='병합 파일 검증',
        epilog='Claude는 이 스크립트의 메타데이터 출력만 확인합니다.'
    )
    parser.add_argument('merged_file', help='검증할 병합 파일 경로')
    parser.add_argument('--expected-sections', type=int,
                        help='예상 섹션 수 (불일치 시 경고)')
    parser.add_argument('--json', action='store_true', help='JSON 형식으로 출력')

    args = parser.parse_args()

    merged_file = Path(args.merged_file)
    result = verify_merge(merged_file, args.expected_sections)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))

    # 종료 코드
    if result["status"] == "error":
        sys.exit(1)
    elif result["status"] == "warning":
        sys.exit(0)  # 경고는 성공으로 처리
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
