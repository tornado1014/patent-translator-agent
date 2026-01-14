#!/usr/bin/env python3
"""
Word Track Changes 피드백 시스템 CLI

검토된 Word 문서에서 피드백을 추출하고 학습 데이터에 반영합니다.

사용법:
    python docx_feedback_cli.py import <docx_path> [--project <name>] [--output <dir>]
    python docx_feedback_cli.py apply <project_name> [--data-dir <path>]
    python docx_feedback_cli.py status <project_name>

명령:
    import  - .docx에서 Track Changes/Comments 추출 및 분류
    apply   - 승인된 피드백을 데이터 파일에 반영
    status  - 프로젝트 피드백 상태 확인

예시:
    python docx_feedback_cli.py import reviewed.docx --project WO2024123456
    python docx_feedback_cli.py apply WO2024123456
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# 현재 스크립트 디렉토리를 path에 추가
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from feedback_models import DocxFeedback, ClassifiedFeedback, FeedbackType  # type: ignore
from extract_docx_feedback import DocxFeedbackExtractor  # type: ignore
from classify_feedback import FeedbackClassifier  # type: ignore
from generate_feedback_report import (
    generate_feedback_report,
    parse_approval_report,
    load_classified_feedback,
)  # type: ignore
from apply_feedback import FeedbackApplier, DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR  # type: ignore


def cmd_import(args: argparse.Namespace) -> int:
    """Word 문서에서 피드백을 추출하고 분류합니다."""

    docx_path = Path(args.docx_path)
    if not docx_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {docx_path}")
        return 1

    # 프로젝트명 결정
    project_name = args.project or docx_path.stem.replace("-reviewed", "").replace(
        "_reviewed", ""
    )

    # 출력 디렉토리
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Word 피드백 임포트 시작 ===")
    print(f"소스 파일: {docx_path}")
    print(f"프로젝트: {project_name}")
    print(f"출력 디렉토리: {output_dir}")

    try:
        # Step 1: Track Changes/Comments 추출
        print(f"\n[1/3] Track Changes 및 Comments 추출 중...")
        extractor = DocxFeedbackExtractor(str(docx_path))
        feedback = extractor.extract()

        print(f"  - 삽입: {feedback.insertion_count}건")
        print(f"  - 삭제: {feedback.deletion_count}건")
        print(f"  - 코멘트: {len(feedback.comments)}건")

        if feedback.total_items == 0:
            print("\nWarning: 추출된 피드백이 없습니다.")
            print("Word 문서에 Track Changes가 활성화되어 있는지 확인하세요.")
            return 0

        # 추출 데이터 저장
        feedback_json_path = output_dir / "feedback-extracted.json"
        with open(feedback_json_path, "w", encoding="utf-8") as f:
            f.write(feedback.to_json())
        print(f"  → 추출 데이터: {feedback_json_path}")

        # Step 2: 피드백 분류
        print(f"\n[2/3] 피드백 분류 중...")
        terminology_db = DEFAULT_DATA_DIR / "terminology-db.md"
        classifier = FeedbackClassifier(
            terminology_db_path=str(terminology_db) if terminology_db.exists() else None
        )
        classified = classifier.classify_all(feedback)

        # 유형별 카운트
        type_counts = {}
        for cf in classified:
            type_name = cf.feedback_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        for type_name, count in sorted(type_counts.items()):
            print(f"  - {type_name}: {count}건")

        # 분류 데이터 저장
        classified_json_path = output_dir / "feedback-classified.json"
        classified_data = {
            "source_file": str(docx_path),
            "extraction_date": feedback.extraction_date.isoformat(),
            "project_name": project_name,
            "classified_feedback": [cf.to_dict() for cf in classified],
        }
        with open(classified_json_path, "w", encoding="utf-8") as f:
            json.dump(classified_data, f, ensure_ascii=False, indent=2)
        print(f"  → 분류 데이터: {classified_json_path}")

        # Step 3: 승인 보고서 생성
        print(f"\n[3/3] 승인 보고서 생성 중...")
        report_path = generate_feedback_report(
            classified,
            project_name,
            str(docx_path),
            str(output_dir),
        )
        print(f"  → 승인 보고서: {report_path}")

        # 완료 메시지
        print(f"\n=== 임포트 완료 ===")
        print(f"총 {len(classified)}건의 피드백이 추출되었습니다.")
        print(f"\n다음 단계:")
        print(f"  1. {report_path} 파일을 열어 검토하세요.")
        print(f"  2. 승인할 항목의 [ ]를 [x]로 변경하세요.")
        print(f"  3. 다음 명령을 실행하세요:")
        print(f"     python docx_feedback_cli.py apply {project_name}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def cmd_apply(args: argparse.Namespace) -> int:
    """승인된 피드백을 데이터 파일에 적용합니다."""

    project_name = args.project_name
    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
    project_dir = DEFAULT_OUTPUT_DIR / project_name

    if not project_dir.exists():
        print(f"Error: 프로젝트 디렉토리가 없습니다: {project_dir}")
        return 1

    print(f"\n=== 피드백 적용 시작 ===")
    print(f"프로젝트: {project_name}")
    print(f"데이터 디렉토리: {data_dir}")

    try:
        # 보고서 파싱
        report_path = project_dir / "feedback-review-report.md"
        if not report_path.exists():
            print(f"Error: 승인 보고서가 없습니다: {report_path}")
            print(f"먼저 import 명령을 실행하세요.")
            return 1

        approvals = parse_approval_report(str(report_path))
        approved_ids = {fid for fid, approved in approvals if approved}
        total_items = len(approvals)

        print(f"\n승인 상태: {len(approved_ids)}/{total_items}건 승인됨")

        if not approved_ids:
            print("\nWarning: 승인된 항목이 없습니다.")
            print("보고서에서 승인할 항목의 [ ]를 [x]로 변경하세요.")
            return 0

        # 분류된 피드백 로드
        classified_path = project_dir / "feedback-classified.json"
        if not classified_path.exists():
            print(f"Error: 분류 데이터가 없습니다: {classified_path}")
            return 1

        classified, _, _ = load_classified_feedback(str(classified_path))

        # 피드백 적용
        print(f"\n피드백 적용 중...")
        applier = FeedbackApplier(project_dir, data_dir)
        result = applier.apply_all(classified, approved_ids)

        # 결과 출력
        print(f"\n=== 적용 완료 ===")
        print(result.to_summary())

        if result.failures:
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """프로젝트 피드백 상태를 확인합니다."""

    project_name = args.project_name
    project_dir = DEFAULT_OUTPUT_DIR / project_name

    if not project_dir.exists():
        print(f"Error: 프로젝트 디렉토리가 없습니다: {project_dir}")
        return 1

    print(f"\n=== 피드백 상태: {project_name} ===")

    # 파일 존재 여부 확인
    extracted_json = project_dir / "feedback-extracted.json"
    classified_json = project_dir / "feedback-classified.json"
    report_md = project_dir / "feedback-review-report.md"

    print(f"\n파일 상태:")
    print(
        f"  - 추출 데이터: {'✓' if extracted_json.exists() else '✗'} {extracted_json.name}"
    )
    print(
        f"  - 분류 데이터: {'✓' if classified_json.exists() else '✗'} {classified_json.name}"
    )
    print(f"  - 승인 보고서: {'✓' if report_md.exists() else '✗'} {report_md.name}")

    if classified_json.exists():
        classified, source_file, extraction_date = load_classified_feedback(
            str(classified_json)
        )

        print(f"\n피드백 요약:")
        print(f"  - 소스: {source_file}")
        print(f"  - 추출 일시: {extraction_date}")
        print(f"  - 총 항목: {len(classified)}건")

        # 유형별 카운트
        type_counts = {}
        for cf in classified:
            type_name = cf.feedback_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        for type_name, count in sorted(type_counts.items()):
            print(f"    - {type_name}: {count}건")

    if report_md.exists():
        approvals = parse_approval_report(str(report_md))
        approved_count = sum(1 for _, approved in approvals if approved)
        print(f"\n승인 상태: {approved_count}/{len(approvals)}건 승인됨")

    return 0


def main() -> int:
    """메인 엔트리포인트"""

    parser = argparse.ArgumentParser(
        description="Word Track Changes 피드백 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="명령")

    # import 명령
    import_parser = subparsers.add_parser("import", help="Word 문서에서 피드백 추출")
    import_parser.add_argument("docx_path", help=".docx 파일 경로")
    import_parser.add_argument("--project", "-p", help="프로젝트명 (기본: 파일명)")
    import_parser.add_argument("--output", "-o", help="출력 디렉토리")

    # apply 명령
    apply_parser = subparsers.add_parser("apply", help="승인된 피드백 적용")
    apply_parser.add_argument("project_name", help="프로젝트명")
    apply_parser.add_argument("--data-dir", help="데이터 디렉토리")

    # status 명령
    status_parser = subparsers.add_parser("status", help="피드백 상태 확인")
    status_parser.add_argument("project_name", help="프로젝트명")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "import":
        return cmd_import(args)
    elif args.command == "apply":
        return cmd_apply(args)
    elif args.command == "status":
        return cmd_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
