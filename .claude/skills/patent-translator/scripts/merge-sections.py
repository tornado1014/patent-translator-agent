#!/usr/bin/env python3
"""
섹션 파일 병합 스크립트 (Token Limit Safe)

이 스크립트는 Claude가 직접 파일을 병합하지 않고,
Python으로 파일 I/O를 처리하여 토큰 제한 문제를 방지합니다.

사용법:
    python merge-sections.py <project_dir> [--json] [--verify]

예시:
    python merge-sections.py output/N90WO1-PCT
    python merge-sections.py output/N90WO1-PCT --json

출력:
    - translation-final.md 생성
    - stdout에 메타데이터 리포트 출력 (파일 내용 아님)

주의:
    Claude는 이 스크립트의 출력(메타데이터)만 확인하고,
    translation-final.md 파일을 직접 읽지 않습니다.

섹션 순서 (한국 특허 표준):
    1. 발명의 명칭 (Title)
    2. 기술분야 (Technical Field + Priority)
    3. 배경기술 (Background)
    4. 도면의 간단한 설명 (Brief Description of Drawings)
    5. 발명을 실시하기 위한 구체적인 내용 (Detailed Description)
    6. 청구범위 (Claims)
    7. 요약서 (Abstract)
"""

import sys
import os
import json
import hashlib
import argparse
import re
from pathlib import Path
from datetime import datetime


# 특허 섹션 순서 정의 (한국 특허 표준)
SECTION_ORDER = [
    "title",       # 발명의 명칭
    "tech_field",  # 기술분야 (우선권 + 기술분야)
    "background",  # 배경기술
    "drawings",    # 도면의 간단한 설명
    "detailed",    # 발명을 실시하기 위한 구체적인 내용
    "claims",      # 청구범위
    "abstract",    # 요약서
]

# 섹션 타입 판별용 패턴
SECTION_PATTERNS = {
    "tac": re.compile(r'section-\d+-tac\.md$', re.IGNORECASE),
    "background": re.compile(r'section-\d+-background\.md$', re.IGNORECASE),
    "drawings": re.compile(r'section-\d+-drawings\.md$', re.IGNORECASE),
    "detailed": re.compile(r'section-\d+[a-z]?-detailed.*\.md$', re.IGNORECASE),
    "claims": re.compile(r'section-\d+-claims\.md$', re.IGNORECASE),
    "abstract": re.compile(r'section-\d+-abstract\.md$', re.IGNORECASE),
    "summary": re.compile(r'section-\d+-summary\.md$', re.IGNORECASE),
}


def extract_translation_content(section_content: str) -> tuple[str, dict]:
    """
    섹션 파일에서 번역문 내용만 추출

    Returns:
        tuple: (추출된 내용, 메타데이터 dict)
    """
    lines = section_content.split('\n')
    original_lines = len(lines)

    # 메타데이터 헤더 건너뛰기 (첫 번째 --- 이후)
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            start_idx = i + 1
            break

    # ## 번역문 섹션 찾기 (있으면)
    in_translation = False
    translation_lines = []

    for line in lines[start_idx:]:
        if '## 번역문' in line:
            in_translation = True
            continue
        if in_translation:
            if line.startswith('## ') or line.strip() == '---':
                break
            translation_lines.append(line)

    # 번역문 섹션이 없으면 전체 내용 사용 (메타데이터 제외)
    if not translation_lines:
        translation_lines = lines[start_idx:]

    extracted = '\n'.join(translation_lines)

    meta = {
        "original_lines": original_lines,
        "extracted_lines": len(translation_lines),
        "original_bytes": len(section_content.encode('utf-8')),
        "extracted_bytes": len(extracted.encode('utf-8'))
    }

    return extracted, meta


def parse_by_markers(content: str) -> dict:
    """
    파일 내용을 【】 마커 기준으로 분리

    Args:
        content: 파일 내용

    Returns:
        dict: {
            "title": 【발명의 명칭】 내용,
            "tech_field": 【기술분야】 내용 (우선권 출원 포함),
            "background": 【배경기술】 내용,
            "drawings": 【도면의 간단한 설명】 내용,
            "detailed": 【발명을 실시하기 위한 구체적인 내용】 내용,
            "claims": 【청구범위】 내용,
            "abstract": 【요약서】 또는 【요약】 내용,
            "priority": 우선권 출원 내용 (마커 없는 경우),
        }
    """
    # 메타데이터 헤더 제거 (첫 번째 --- 이후부터 시작)
    lines = content.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            start_idx = i + 1
            break

    body = '\n'.join(lines[start_idx:])

    result = {
        "title": "",
        "tech_field": "",
        "background": "",
        "drawings": "",
        "detailed": "",
        "claims": "",
        "abstract": "",
        "priority": "",  # 우선권 출원 (마커 없는 텍스트)
    }

    # 마커와 타입 매핑
    marker_map = {
        "【발명의 명칭】": "title",
        "【기술분야】": "tech_field",
        "【배경기술】": "background",
        "【도면의 간단한 설명】": "drawings",
        "【발명을 실시하기 위한 구체적인 내용】": "detailed",
        "【청구범위】": "claims",
        "【요약서】": "abstract",
        "【요약】": "abstract",
    }

    # 모든 마커 위치 찾기
    marker_positions = []
    for marker, sec_type in marker_map.items():
        pos = body.find(marker)
        if pos != -1:
            marker_positions.append((pos, marker, sec_type))

    # 위치순 정렬
    marker_positions.sort(key=lambda x: x[0])

    # 첫 마커 전의 내용 (우선권 출원 등)
    if marker_positions:
        first_pos = marker_positions[0][0]
        priority_content = body[:first_pos].strip()
        # --- 구분자 제거
        priority_content = priority_content.replace('---', '').strip()
        if priority_content:
            result["priority"] = priority_content

    # 각 마커별 내용 추출
    for i, (pos, marker, sec_type) in enumerate(marker_positions):
        # 다음 마커까지 또는 끝까지
        if i + 1 < len(marker_positions):
            next_pos = marker_positions[i + 1][0]
            section_content = body[pos:next_pos]
        else:
            section_content = body[pos:]

        # 끝의 --- 제거
        section_content = section_content.strip()
        while section_content.endswith('---'):
            section_content = section_content[:-3].strip()

        # 【발명의 명칭】 특수 처리: 첫 번째 --- 이후 내용은 priority로 분리
        if sec_type == "title" and '---' in section_content:
            parts = section_content.split('---', 1)
            title_part = parts[0].strip()
            remainder = parts[1].strip() if len(parts) > 1 else ""

            # 남은 내용에서 또 --- 가 있으면 제거
            while remainder.endswith('---'):
                remainder = remainder[:-3].strip()

            # 남은 내용이 다른 마커로 시작하지 않으면 priority로 저장
            if remainder and not any(remainder.startswith(m) for m in marker_map.keys()):
                if result["priority"]:
                    result["priority"] += '\n\n' + remainder
                else:
                    result["priority"] = remainder

            section_content = title_part

        # 이미 같은 타입에 내용이 있으면 추가
        if result[sec_type]:
            result[sec_type] += '\n\n' + section_content
        else:
            result[sec_type] = section_content

    return result


def merge_priority_into_tech_field(parsed: dict) -> dict:
    """
    우선권 출원 내용을 기술분야에 병합 (한국 특허 표준 형식)

    예시 파일 구조:
    【기술분야】
    우선권 출원
    ...
    기술분야
    ...

    Args:
        parsed: parse_by_markers 결과

    Returns:
        dict: 병합된 결과
    """
    result = parsed.copy()

    # 우선권 내용이 있으면 기술분야 앞에 추가
    if result["priority"]:
        if result["tech_field"]:
            # 기존 기술분야에서 【기술분야】 헤더 제거
            tech_content = result["tech_field"]
            if tech_content.startswith("【기술분야】"):
                tech_content = tech_content[len("【기술분야】"):].strip()

            # 【기술분야】 헤더 + 우선권 + "기술분야" 소제목 + 기술분야 본문
            result["tech_field"] = (
                f"【기술분야】\n\n"
                f"{result['priority']}\n\n"
                f"기술분야\n\n"
                f"{tech_content}"
            )
        else:
            # 기술분야 본문이 없으면 우선권만
            result["tech_field"] = f"【기술분야】\n\n{result['priority']}"
        result["priority"] = ""  # 이미 병합됨

    return result


def get_section_type(filename: str) -> str:
    """파일명에서 섹션 타입 판별"""
    for sec_type, pattern in SECTION_PATTERNS.items():
        if pattern.search(filename):
            return sec_type
    return "unknown"


def merge_sections(project_dir: Path, output_file: str = 'translation-final.md') -> dict:
    """
    섹션 파일들을 병합하고 메타데이터 반환

    Args:
        project_dir: 프로젝트 디렉토리 경로
        output_file: 출력 파일 이름 (기본: translation-final.md)

    Returns:
        dict: 병합 결과 메타데이터
            - status: "success" 또는 "error"
            - project: 프로젝트 이름
            - sections_merged: 병합된 섹션 수
            - sections: 각 섹션별 메타데이터 리스트
            - output_file: 출력 파일 경로
            - total_lines: 총 라인 수
            - total_bytes: 총 바이트 수
            - hash: SHA256 해시 (앞 16자리)
    """

    sections_dir = project_dir / 'sections'

    try:
        if not sections_dir.exists():
            return {
                "status": "error",
                "message": f"sections 폴더를 찾을 수 없습니다: {sections_dir}"
            }
    except PermissionError:
        return {
            "status": "error",
            "message": f"sections 폴더 접근 권한이 없습니다: {sections_dir}",
            "file": str(sections_dir)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"sections 폴더 확인 실패: {sections_dir} - {str(e)}",
            "file": str(sections_dir)
        }

    # 섹션 파일 수집 및 정렬 (section-01, section-02, section-04a, ...)
    try:
        section_files = sorted(sections_dir.glob('section-*.md'))
    except PermissionError:
        return {
            "status": "error",
            "message": f"sections 폴더 읽기 권한이 없습니다: {sections_dir}",
            "file": str(sections_dir)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"섹션 파일 검색 실패: {sections_dir} - {str(e)}",
            "file": str(sections_dir)
        }

    if not section_files:
        return {
            "status": "error",
            "message": f"섹션 파일을 찾을 수 없습니다: {sections_dir}"
        }

    # 섹션 타입별 내용 저장소
    # SECTION_ORDER: title, tech_field, background, drawings, detailed, claims, abstract
    ordered_sections = {sec_type: [] for sec_type in SECTION_ORDER}

    # 메타데이터 수집
    sections_meta = []

    # 모든 파일을 마커 기반으로 파싱
    all_parsed = {}
    for sf in section_files:
        try:
            content = sf.read_text(encoding='utf-8')
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"섹션 파일을 찾을 수 없습니다: {sf}",
                "file": str(sf)
            }
        except PermissionError:
            return {
                "status": "error",
                "message": f"섹션 파일 읽기 권한이 없습니다: {sf}",
                "file": str(sf)
            }
        except UnicodeDecodeError:
            return {
                "status": "error",
                "message": f"섹션 파일 인코딩 오류 (UTF-8 필요): {sf}",
                "file": str(sf)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"섹션 파일 읽기 실패: {sf} - {str(e)}",
                "file": str(sf)
            }

        parsed = parse_by_markers(content)
        all_parsed[sf.name] = parsed

        # 메타데이터 기록
        found_types = [k for k, v in parsed.items() if v and k != "priority"]
        sections_meta.append({
            "name": sf.name,
            "found_sections": found_types,
            "original_bytes": len(content.encode('utf-8'))
        })

    # 우선권 출원을 기술분야에 병합
    for fname, parsed in all_parsed.items():
        if parsed["priority"]:
            all_parsed[fname] = merge_priority_into_tech_field(parsed)

    # 각 타입별로 내용 수집 (파일 순서 유지)
    for sf in section_files:
        parsed = all_parsed[sf.name]
        for sec_type in SECTION_ORDER:
            if parsed.get(sec_type):
                ordered_sections[sec_type].append(parsed[sec_type])

    # 마커-헤더 매핑 (중복 제거용)
    type_headers = {
        "title": "【발명의 명칭】",
        "tech_field": "【기술분야】",
        "background": "【배경기술】",
        "drawings": "【도면의 간단한 설명】",
        "detailed": "【발명을 실시하기 위한 구체적인 내용】",
        "claims": "【청구범위】",
        "abstract": "【요약서】",
    }

    # 정의된 순서대로 병합
    merged_parts = []
    section_order_info = []

    for sec_type in SECTION_ORDER:
        if ordered_sections[sec_type]:
            # 같은 타입 내에서 중복 헤더 제거 후 연결
            header = type_headers.get(sec_type, "")
            parts_without_dup_header = []

            for idx, part in enumerate(ordered_sections[sec_type]):
                if idx == 0:
                    # 첫 번째는 그대로
                    parts_without_dup_header.append(part)
                else:
                    # 두 번째부터는 헤더 제거
                    if header and part.startswith(header):
                        part = part[len(header):].strip()
                        # 기술분야의 경우 소제목 추가 (예시 파일 형식)
                        if sec_type == "tech_field":
                            part = f"기술분야\n\n{part}"
                    parts_without_dup_header.append(part)

            combined = '\n\n'.join(parts_without_dup_header)
            merged_parts.append(combined)
            section_order_info.append({
                "type": sec_type,
                "count": len(ordered_sections[sec_type]),
                "bytes": len(combined.encode('utf-8'))
            })

    # 병합 (섹션 구분자로 연결)
    merged_content = '\n\n---\n\n'.join(merged_parts)

    # 저장
    output_path = project_dir / output_file
    try:
        output_path.write_text(merged_content, encoding='utf-8')
    except PermissionError:
        return {
            "status": "error",
            "message": f"출력 파일 쓰기 권한이 없습니다: {output_path}",
            "file": str(output_path)
        }
    except OSError as e:
        return {
            "status": "error",
            "message": f"출력 파일 쓰기 실패: {output_path} - {str(e)}",
            "file": str(output_path)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"예상치 못한 쓰기 오류: {output_path} - {str(e)}",
            "file": str(output_path)
        }

    # 해시 계산
    file_hash = hashlib.sha256(merged_content.encode('utf-8')).hexdigest()[:16]

    return {
        "status": "success",
        "project": project_dir.name,
        "files_processed": len(section_files),
        "section_order": section_order_info,
        "files": sections_meta,
        "output_file": str(output_path),
        "total_lines": len(merged_content.split('\n')),
        "total_bytes": len(merged_content.encode('utf-8')),
        "hash": f"sha256:{file_hash}",
        "timestamp": datetime.now().isoformat()
    }


def format_report(result: dict) -> str:
    """결과를 사람이 읽기 쉬운 형식으로 포맷"""

    if result["status"] != "success":
        return f"[MERGE_FAILED] {result.get('message', 'Unknown error')}"

    # 섹션 타입 한글 매핑
    type_names = {
        "title": "발명의 명칭",
        "tech_field": "기술분야",
        "background": "배경기술",
        "drawings": "도면의 간단한 설명",
        "detailed": "발명을 실시하기 위한 구체적인 내용",
        "claims": "청구범위",
        "abstract": "요약서",
    }

    lines = [
        "[MERGE_SUCCESS] 병합 완료 (한국 특허 표준 순서)",
        f"  프로젝트: {result['project']}",
        f"  처리 파일: {result['files_processed']}개",
        f"  총 라인: {result['total_lines']:,}",
        f"  파일 크기: {result['total_bytes']:,} bytes",
        f"  해시: {result['hash']}",
        f"  출력: {result['output_file']}",
        "",
        "  섹션 순서 (병합 결과):"
    ]

    for idx, sec in enumerate(result.get('section_order', []), 1):
        type_name = type_names.get(sec['type'], sec['type'])
        lines.append(f"    {idx}. {type_name}: {sec['bytes']:,} bytes")

    lines.append("")
    lines.append("  처리된 파일:")
    for f in result.get('files', []):
        if f.get('type') == 'tac (분리됨)':
            lines.append(f"    - {f['name']}: TAC → title/tech_field/claims/abstract로 분리")
        else:
            extracted = f.get('extracted_lines', '?')
            bytes_size = f.get('extracted_bytes', '?')
            lines.append(f"    - {f['name']}: {extracted} lines → {f.get('type', 'unknown')}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='섹션 파일 병합 (Token Limit Safe)',
        epilog='Claude는 이 스크립트의 메타데이터 출력만 확인합니다.'
    )
    parser.add_argument('project_dir', help='프로젝트 디렉토리 경로')
    parser.add_argument('--json', action='store_true', help='JSON 형식으로 출력')
    parser.add_argument('--output', '-o', default='translation-final.md',
                        help='출력 파일 이름 (기본: translation-final.md)')

    args = parser.parse_args()

    project_dir = Path(args.project_dir)

    if not project_dir.exists():
        error = {"status": "error", "message": f"프로젝트 디렉토리를 찾을 수 없습니다: {project_dir}"}
        if args.json:
            print(json.dumps(error, ensure_ascii=False, indent=2))
        else:
            print(f"[ERROR] {error['message']}")
        sys.exit(1)

    result = merge_sections(project_dir, args.output)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))

    if result["status"] != "success":
        sys.exit(1)


if __name__ == '__main__':
    main()
