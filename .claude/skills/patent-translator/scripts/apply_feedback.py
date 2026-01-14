#!/usr/bin/env python3
"""
승인된 피드백 적용기

승인 보고서에서 체크된 항목을 데이터 파일에 반영합니다.

대상 파일:
- terminology-db.md: 용어 추가/수정
- error-patterns.md: 오류 패턴 추가
- feedback-log.md: 모든 피드백 로깅
- project-tb.md: 프로젝트 TB 업데이트

사용법:
    python apply_feedback.py <project_name> [--data-dir <path>]
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set

# 현재 스크립트 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feedback_models import ClassifiedFeedback, FeedbackType, ApplyResult  # type: ignore
from generate_feedback_report import parse_approval_report, load_classified_feedback  # type: ignore


# 기본 경로
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent.parent / "output"


class FeedbackApplier:
    """승인된 피드백을 데이터 파일에 적용합니다."""

    def __init__(
        self,
        project_dir: Path,
        data_dir: Path,
    ):
        self.project_dir = Path(project_dir)
        self.data_dir = Path(data_dir)
        self.result = ApplyResult()

        # 데이터 파일 경로
        self.terminology_db_path = self.data_dir / "terminology-db.md"
        self.error_patterns_path = self.data_dir / "error-patterns.md"
        self.feedback_log_path = self.data_dir / "feedback-log.md"
        self.project_tb_path = self.project_dir / "project-tb.md"

    def apply_all(
        self,
        classified_feedback: List[ClassifiedFeedback],
        approved_ids: Set[int],
    ) -> ApplyResult:
        """승인된 피드백을 모두 적용합니다."""

        for cf in classified_feedback:
            if cf.id not in approved_ids:
                continue

            try:
                self._apply_single(cf)
            except Exception as e:
                self.result.failures.append(f"[{cf.id}] {str(e)}")

        return self.result

    def _apply_single(self, cf: ClassifiedFeedback) -> None:
        """단일 피드백을 적용합니다."""

        if cf.feedback_type == FeedbackType.TERMINOLOGY:
            self._apply_terminology(cf)
        elif cf.feedback_type == FeedbackType.ERROR:
            self._apply_error_pattern(cf)
        elif cf.feedback_type == FeedbackType.STYLE:
            self._apply_style(cf)
        else:
            self._apply_other(cf)

        # 모든 피드백은 feedback-log에 기록
        self._log_feedback(cf)

    def _apply_terminology(self, cf: ClassifiedFeedback) -> None:
        """용어를 terminology-db.md에 추가합니다."""

        if not cf.original_text or not cf.suggested_text:
            return

        # 기존 용어집 로드
        if self.terminology_db_path.exists():
            content = self.terminology_db_path.read_text(encoding="utf-8")
        else:
            content = self._create_terminology_template()

        # 중복 검사
        if cf.original_text.lower() in content.lower():
            # 이미 존재하면 업데이트로 처리
            self.result.terminology_updated += 1
            return

        # 새 용어 추가
        new_entry = f"| {cf.original_text} | {cf.suggested_text} | 피드백 추가 ({datetime.now().strftime('%Y-%m-%d')}) |"

        # 테이블 끝에 추가
        if "| English | Korean |" in content or "| 영문 | 한글 |" in content:
            # 기존 테이블에 추가
            lines = content.split("\n")
            insert_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("|") and not line.strip().startswith("|---"):
                    insert_idx = i + 1

            if insert_idx > 0:
                lines.insert(insert_idx, new_entry)
                content = "\n".join(lines)
        else:
            # 테이블이 없으면 새로 생성
            content += f"\n\n## 피드백 추가 용어\n\n| English | Korean | 비고 |\n|---------|--------|------|\n{new_entry}\n"

        self.terminology_db_path.write_text(content, encoding="utf-8")
        self.result.terminology_added += 1

        # project-tb.md도 업데이트
        self._update_project_tb(cf)

    def _apply_error_pattern(self, cf: ClassifiedFeedback) -> None:
        """오류 패턴을 error-patterns.md에 추가합니다."""

        if self.error_patterns_path.exists():
            content = self.error_patterns_path.read_text(encoding="utf-8")
        else:
            content = self._create_error_patterns_template()

        # 새 패턴 추가
        severity = "중" if cf.confidence > 0.7 else "하"
        new_entry = f"| {cf.original_text[:50]} | {cf.suggested_text[:50]} | {severity} | {cf.classification_reason} |"

        # 피드백 섹션 찾기 또는 생성
        if "## 피드백 기반 패턴" in content:
            # 기존 섹션에 추가
            idx = content.find("## 피드백 기반 패턴")
            table_end = content.find("\n\n", idx + 50)
            if table_end == -1:
                table_end = len(content)

            content = content[:table_end] + f"\n{new_entry}" + content[table_end:]
        else:
            # 새 섹션 생성
            content += f"\n\n## 피드백 기반 패턴\n\n| 원문 | 수정 | 심각도 | 설명 |\n|------|------|--------|------|\n{new_entry}\n"

        self.error_patterns_path.write_text(content, encoding="utf-8")
        self.result.errors_added += 1

    def _apply_style(self, cf: ClassifiedFeedback) -> None:
        """스타일 피드백을 feedback-log.md에 기록합니다."""
        # _log_feedback에서 처리됨
        self.result.styles_logged += 1

    def _apply_other(self, cf: ClassifiedFeedback) -> None:
        """기타 피드백을 feedback-log.md에 기록합니다."""
        # _log_feedback에서 처리됨
        pass

    def _log_feedback(self, cf: ClassifiedFeedback) -> None:
        """피드백을 feedback-log.md에 기록합니다."""

        if self.feedback_log_path.exists():
            content = self.feedback_log_path.read_text(encoding="utf-8")
        else:
            content = self._create_feedback_log_template()

        # 새 피드백 기록
        today = datetime.now().strftime("%Y-%m-%d")
        project_name = self.project_dir.name

        new_entry = f"""
### [{today}] {project_name}

**피드백 유형**: {cf.feedback_type.value}
**원문**: {cf.original_text}
**수정 번역**: {cf.suggested_text}
**사유**: {cf.classification_reason}
**반영 상태**: 완료
**영향 범위**: {", ".join(cf.target_files)}

---
"""

        # "## 피드백 기록" 섹션 다음에 추가
        if "## 피드백 기록" in content:
            idx = content.find("## 피드백 기록")
            next_section = content.find("\n##", idx + 20)
            if next_section == -1:
                next_section = len(content)

            # 섹션 헤더 다음에 삽입
            header_end = content.find("\n", idx)
            content = content[: header_end + 1] + new_entry + content[header_end + 1 :]
        else:
            content += f"\n## 피드백 기록\n{new_entry}"

        self.feedback_log_path.write_text(content, encoding="utf-8")

        # 통계 업데이트
        self._update_feedback_stats(content)

    def _update_project_tb(self, cf: ClassifiedFeedback) -> None:
        """project-tb.md를 업데이트합니다."""

        if not self.project_tb_path.exists():
            return

        content = self.project_tb_path.read_text(encoding="utf-8")

        # 중복 검사
        if cf.original_text.lower() in content.lower():
            return

        # 피드백 섹션 추가
        new_entry = (
            f"| {cf.original_text} | {cf.suggested_text} | 피드백 | 피드백 반영 |"
        )

        if "## 피드백 추가 용어" in content:
            idx = content.find("## 피드백 추가 용어")
            table_end = content.find("\n\n", idx + 50)
            if table_end == -1:
                table_end = len(content)

            content = content[:table_end] + f"\n{new_entry}" + content[table_end:]
        else:
            content += f"\n\n## 피드백 추가 용어\n\n| English | Korean | 첫 등장 | 비고 |\n|---------|--------|---------|------|\n{new_entry}\n"

        self.project_tb_path.write_text(content, encoding="utf-8")
        self.result.project_tb_updated += 1

    def _update_feedback_stats(self, content: str) -> None:
        """feedback-log.md의 통계를 업데이트합니다."""
        # 간단한 통계 업데이트 (정규식으로 카운트)
        # 실제 구현에서는 더 정교한 파싱 필요
        pass

    def _create_terminology_template(self) -> str:
        """terminology-db.md 템플릿을 생성합니다."""
        return """# 용어집 (Terminology Database)

> 영한 특허번역 용어집

## 일반 용어

| English | Korean | 비고 |
|---------|--------|------|
"""

    def _create_error_patterns_template(self) -> str:
        """error-patterns.md 템플릿을 생성합니다."""
        return """# 오류 패턴 (Error Patterns)

> 번역 시 주의해야 할 오류 패턴

## 상기 (Antecedent Basis)

| 원문 | 잘못된 번역 | 올바른 번역 | 심각도 |
|------|-------------|-------------|--------|
"""

    def _create_feedback_log_template(self) -> str:
        """feedback-log.md 템플릿을 생성합니다."""
        return """# 피드백 로그 (Feedback Log)

> 사용자 피드백을 기록하여 시스템 학습에 활용

## 피드백 기록

"""


def main() -> int:
    """CLI 엔트리포인트"""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    project_name = sys.argv[1]

    # 경로 설정
    data_dir = DEFAULT_DATA_DIR
    output_dir = DEFAULT_OUTPUT_DIR

    # 명령줄 옵션 파싱
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--data-dir" and i + 1 < len(sys.argv):
            data_dir = Path(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--output-dir" and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    project_dir = output_dir / project_name

    try:
        # 보고서 파싱
        report_path = project_dir / "feedback-review-report.md"
        if not report_path.exists():
            print(f"Error: 보고서 파일이 없습니다: {report_path}")
            print(f"먼저 /import-feedback-docx {project_name} 명령을 실행하세요.")
            return 1

        approvals = parse_approval_report(str(report_path))
        approved_ids = {fid for fid, approved in approvals if approved}

        if not approved_ids:
            print("Warning: 승인된 항목이 없습니다.")
            print("보고서에서 승인할 항목의 [ ]를 [x]로 변경하세요.")
            return 0

        # 분류된 피드백 로드
        classified_path = project_dir / "feedback-classified.json"
        if not classified_path.exists():
            # fallback: .feedback.json 파일 찾기
            json_files = list(project_dir.glob("*.classified.json"))
            if json_files:
                classified_path = json_files[0]
            else:
                print(f"Error: 분류된 피드백 파일이 없습니다.")
                return 1

        classified, _, _ = load_classified_feedback(str(classified_path))

        # 피드백 적용
        applier = FeedbackApplier(project_dir, data_dir)
        result = applier.apply_all(classified, approved_ids)

        # 결과 출력
        print(f"\n=== 피드백 적용 완료 ===")
        print(result.to_summary())

        if result.failures:
            print(f"\n실패한 항목:")
            for f in result.failures:
                print(f"  - {f}")
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
