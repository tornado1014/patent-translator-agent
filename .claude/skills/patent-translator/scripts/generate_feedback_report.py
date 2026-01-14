#!/usr/bin/env python3
"""
피드백 승인 보고서 생성기

분류된 피드백을 체크박스 기반 승인 보고서로 생성합니다.

사용법:
    python generate_feedback_report.py <classified.json> <project_name> [output_dir]
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# 현재 스크립트 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feedback_models import ClassifiedFeedback, FeedbackType  # type: ignore


def generate_feedback_report(
    classified_feedback: List[ClassifiedFeedback],
    project_name: str,
    source_file: str,
    output_dir: str,
) -> str:
    """
    분류된 피드백을 승인 보고서로 생성합니다.

    Args:
        classified_feedback: 분류된 피드백 목록
        project_name: 프로젝트 이름
        source_file: 원본 docx 파일명
        output_dir: 출력 디렉토리

    Returns:
        생성된 보고서 파일 경로
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_file = output_path / "feedback-review-report.md"

    # 유형별 분류
    by_type: Dict[FeedbackType, List[ClassifiedFeedback]] = {
        FeedbackType.TERMINOLOGY: [],
        FeedbackType.ERROR: [],
        FeedbackType.STYLE: [],
        FeedbackType.OTHER: [],
    }

    for cf in classified_feedback:
        by_type[cf.feedback_type].append(cf)

    # 보고서 생성
    lines: List[str] = []

    # 헤더
    lines.append("# 피드백 검토 보고서 (Feedback Review Report)")
    lines.append("")
    lines.append(f"**프로젝트**: {project_name}")
    lines.append(f"**원본 파일**: {source_file}")
    lines.append(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 요약
    lines.append("## 요약 (Summary)")
    lines.append("")
    lines.append(f"- **총 피드백**: {len(classified_feedback)}건")
    lines.append(
        f"  - 용어 수정 (Terminology): {len(by_type[FeedbackType.TERMINOLOGY])}건"
    )
    lines.append(f"  - 오류 수정 (Error): {len(by_type[FeedbackType.ERROR])}건")
    lines.append(f"  - 스타일 개선 (Style): {len(by_type[FeedbackType.STYLE])}건")
    lines.append(f"  - 기타 (Other): {len(by_type[FeedbackType.OTHER])}건")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 사용 안내
    lines.append("## 사용 방법")
    lines.append("")
    lines.append("1. 각 항목을 검토하고 승인할 항목의 `[ ]`를 `[x]`로 변경하세요.")
    lines.append("2. 모든 검토가 완료되면 저장합니다.")
    lines.append("3. `/apply-feedback-docx` 명령으로 승인된 항목을 반영합니다.")
    lines.append("")
    lines.append("```")
    lines.append(f"/apply-feedback-docx {project_name}")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 용어 수정 섹션
    if by_type[FeedbackType.TERMINOLOGY]:
        lines.append("## 용어 수정 (Terminology)")
        lines.append("")
        lines.append("> 승인 시 `terminology-db.md` 및 `project-tb.md`에 반영됩니다.")
        lines.append("")

        for cf in by_type[FeedbackType.TERMINOLOGY]:
            lines.extend(_format_feedback_item(cf))

        lines.append("---")
        lines.append("")

    # 오류 수정 섹션
    if by_type[FeedbackType.ERROR]:
        lines.append("## 오류 수정 (Error Corrections)")
        lines.append("")
        lines.append("> 승인 시 `error-patterns.md`에 패턴으로 기록됩니다.")
        lines.append("")

        for cf in by_type[FeedbackType.ERROR]:
            lines.extend(_format_feedback_item(cf))

        lines.append("---")
        lines.append("")

    # 스타일 개선 섹션
    if by_type[FeedbackType.STYLE]:
        lines.append("## 스타일 개선 (Style Preferences)")
        lines.append("")
        lines.append("> 승인 시 `feedback-log.md`에 기록됩니다.")
        lines.append("")

        for cf in by_type[FeedbackType.STYLE]:
            lines.extend(_format_feedback_item(cf))

        lines.append("---")
        lines.append("")

    # 기타 섹션
    if by_type[FeedbackType.OTHER]:
        lines.append("## 기타 (Other)")
        lines.append("")
        lines.append("> 승인 시 `feedback-log.md`에 기록됩니다.")
        lines.append("")

        for cf in by_type[FeedbackType.OTHER]:
            lines.extend(_format_feedback_item(cf))

        lines.append("---")
        lines.append("")

    # 푸터
    lines.append("## 다음 단계")
    lines.append("")
    lines.append("검토 완료 후 다음 명령을 실행하세요:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/apply-feedback-docx {project_name}")
    lines.append("```")
    lines.append("")
    lines.append("또는 CLI에서:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"python docx_feedback_cli.py apply {project_name}")
    lines.append("```")
    lines.append("")

    # 파일 저장
    content = "\n".join(lines)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)

    return str(report_file)


def _format_feedback_item(cf: ClassifiedFeedback) -> List[str]:
    """개별 피드백 항목을 마크다운으로 포맷합니다."""
    lines: List[str] = []

    # 제목 (원문 → 수정)
    if cf.original_text and cf.suggested_text:
        title = f"`{_truncate(cf.original_text, 30)}` → `{_truncate(cf.suggested_text, 30)}`"
    elif cf.suggested_text:
        title = f"추가: `{_truncate(cf.suggested_text, 50)}`"
    elif cf.original_text:
        title = f"삭제: `{_truncate(cf.original_text, 50)}`"
    else:
        title = "(내용 없음)"

    lines.append(f"### [{cf.id}] {title}")
    lines.append("")

    # 메타데이터
    conf_pct = int(cf.confidence * 100)
    lines.append(f"- **유형**: {cf.feedback_type.value}")
    lines.append(f"- **신뢰도**: {conf_pct}%")
    lines.append(f"- **작성자**: {cf.author}")
    lines.append(f"- **소스**: {cf.source_type}")

    # 상세 내용
    if cf.original_text:
        lines.append(f"- **원문**: {_escape_md(cf.original_text)}")
    if cf.suggested_text:
        lines.append(f"- **수정**: {_escape_md(cf.suggested_text)}")

    # 컨텍스트
    if cf.context:
        lines.append(f"- **위치**: {_escape_md(cf.context)}")

    # 분류 사유
    lines.append(f"- **분류 사유**: {cf.classification_reason}")

    # 대상 파일
    target_files_str = ", ".join(f"`{f}`" for f in cf.target_files)
    lines.append(f"- **반영 대상**: {target_files_str}")

    lines.append("")

    # 승인 체크박스
    lines.append(f"- [ ] 승인 (ID: {cf.id})")
    lines.append("")

    return lines


def _truncate(text: str, max_len: int) -> str:
    """텍스트를 지정된 길이로 자릅니다."""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _escape_md(text: str) -> str:
    """마크다운 특수문자를 이스케이프합니다."""
    text = text.replace("\n", " ").strip()
    # 백틱, 파이프 등 이스케이프
    text = text.replace("`", "'")
    text = text.replace("|", "\\|")
    return text


def parse_approval_report(report_path: str) -> List[Tuple[int, bool]]:
    """
    승인 보고서를 파싱하여 승인된 항목 ID 목록을 반환합니다.

    Returns:
        [(feedback_id, approved), ...]
    """
    results: List[Tuple[int, bool]] = []

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 체크박스 패턴 매칭: - [x] 승인 (ID: 123) 또는 - [ ] 승인 (ID: 123)
    pattern = r"-\s*\[([ xX])\]\s*승인\s*\(ID:\s*(\d+)\)"

    for match in re.finditer(pattern, content):
        checked = match.group(1).lower() == "x"
        feedback_id = int(match.group(2))
        results.append((feedback_id, checked))

    return results


def load_classified_feedback(
    json_path: str,
) -> Tuple[List[ClassifiedFeedback], str, str]:
    """
    분류된 피드백 JSON을 로드합니다.

    Returns:
        (classified_feedback_list, source_file, extraction_date)
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    classified = [
        ClassifiedFeedback.from_dict(item)
        for item in data.get("classified_feedback", [])
    ]

    return (
        classified,
        data.get("source_file", "unknown"),
        data.get("extraction_date", ""),
    )


def main() -> int:
    """CLI 엔트리포인트"""
    if len(sys.argv) < 3:
        print(__doc__)
        print(
            "\n사용법: python generate_feedback_report.py <classified.json> <project_name> [output_dir]"
        )
        return 1

    classified_path = sys.argv[1]
    project_name = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else f"output/{project_name}"

    try:
        # 분류된 피드백 로드
        classified, source_file, _ = load_classified_feedback(classified_path)

        if not classified:
            print("Warning: 분류된 피드백이 없습니다.")
            return 0

        # 보고서 생성
        report_path = generate_feedback_report(
            classified,
            project_name,
            source_file,
            output_dir,
        )

        print(f"\n=== 피드백 검토 보고서 생성 완료 ===")
        print(f"프로젝트: {project_name}")
        print(f"총 항목: {len(classified)}건")
        print(f"보고서: {report_path}")
        print(f"\n다음 단계:")
        print(f"  1. {report_path} 파일을 열어 검토하세요.")
        print(f"  2. 승인할 항목의 [ ]를 [x]로 변경하세요.")
        print(f"  3. /apply-feedback-docx {project_name} 명령을 실행하세요.")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
