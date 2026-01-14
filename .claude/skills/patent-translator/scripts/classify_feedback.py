#!/usr/bin/env python3
"""
피드백 자동 분류기

추출된 Track Changes와 Comments를 피드백 유형별로 분류합니다.
- terminology: 용어 수정
- error: 오류 수정 (상기 누락, 참조부호 등)
- style: 스타일/표현 개선
- other: 기타

사용법:
    python classify_feedback.py <feedback.json> [output.json]
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

# 현재 스크립트 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feedback_models import (  # type: ignore
    TrackChange,
    Comment,
    DocxFeedback,
    ClassifiedFeedback,
    FeedbackType,
    ChangeType,
)


# 분류 패턴 정의
TERMINOLOGY_PATTERNS = [
    (r"→|->|=>", 0.9),  # 화살표 (용어 대체 표시)
    (r"[가-힣]+\s*[/|]\s*[가-힣]+", 0.8),  # 한글/한글 형식
    (r"번역|translation|term", 0.7),
    (r"용어|terminology", 0.8),
    (r"[A-Za-z]+\s*[:=]\s*[가-힣]+", 0.85),  # English: 한글
]

ERROR_PATTERNS = [
    (r"상기", 0.9),  # 상기 관련
    (r"오류|error|mistake|wrong", 0.85),
    (r"누락|missing|omit", 0.85),
    (r"잘못|incorrect", 0.8),
    (r"참조\s*부호|reference\s*numeral|\(\d+\)", 0.75),
    (r"antecedent", 0.9),
]

STYLE_PATTERNS = [
    (r"표현|expression|phrasing", 0.8),
    (r"자연스럽|natural|fluent", 0.85),
    (r"어색|awkward|unnatural", 0.85),
    (r"문체|style|tone", 0.75),
    (r"더\s*좋|better|prefer", 0.7),
]

# 단어 수준 변경 (용어 수정 후보)
WORD_LEVEL_THRESHOLD = 5  # 5단어 이하면 용어 수정으로 간주


class FeedbackClassifier:
    """피드백 자동 분류기"""

    def __init__(self, terminology_db_path: Optional[str] = None):
        """
        Args:
            terminology_db_path: 기존 용어집 파일 경로 (중복 검사용)
        """
        self.existing_terms: Dict[str, str] = {}
        if terminology_db_path and Path(terminology_db_path).exists():
            self._load_terminology_db(terminology_db_path)

    def _load_terminology_db(self, path: str) -> None:
        """기존 용어집을 로드합니다."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # 마크다운 테이블에서 용어 추출 (| English | Korean | 형식)
            for line in content.split("\n"):
                if "|" in line and not line.strip().startswith("|---"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        english = parts[1].lower()
                        korean = parts[2]
                        if english and korean and not english.startswith("english"):
                            self.existing_terms[english] = korean
        except Exception:
            pass  # 용어집 로드 실패는 무시

    def classify_all(self, feedback: DocxFeedback) -> List[ClassifiedFeedback]:
        """모든 피드백을 분류합니다."""
        classified: List[ClassifiedFeedback] = []
        feedback_id = 0

        # Track Changes 분류
        # 삭제+삽입 쌍을 먼저 매칭
        paired_changes = self._pair_changes(feedback.track_changes)

        for original, suggested, para_idx, author in paired_changes:
            feedback_id += 1
            classified.append(
                self._classify_change_pair(
                    feedback_id, original, suggested, para_idx, author
                )
            )

        # 단독 삽입/삭제 처리
        paired_indices = set()
        for original, suggested, para_idx, _ in paired_changes:
            # 이미 페어링된 변경은 스킵
            pass

        # Comments 분류
        for comment in feedback.comments:
            feedback_id += 1
            classified.append(self._classify_comment(feedback_id, comment))

        return classified

    def _pair_changes(
        self, changes: List[TrackChange]
    ) -> List[Tuple[str, str, int, str]]:
        """
        같은 문단에서 삭제 직후 삽입이 있으면 쌍으로 매칭합니다.
        반환: [(원문, 수정문, 문단인덱스, 작성자), ...]
        """
        pairs: List[Tuple[str, str, int, str]] = []
        used_indices: set = set()

        for i, change in enumerate(changes):
            if i in used_indices:
                continue

            if change.change_type == ChangeType.DELETION:
                # 같은 문단에서 바로 다음 삽입 찾기
                for j, next_change in enumerate(changes[i + 1 :], start=i + 1):
                    if j in used_indices:
                        continue

                    if (
                        next_change.change_type == ChangeType.INSERTION
                        and next_change.paragraph_index == change.paragraph_index
                    ):
                        # 쌍 매칭
                        pairs.append(
                            (
                                change.text,  # 삭제된 텍스트 (원문)
                                next_change.text,  # 삽입된 텍스트 (수정)
                                change.paragraph_index,
                                change.author,
                            )
                        )
                        used_indices.add(i)
                        used_indices.add(j)
                        break

            # 매칭되지 않은 변경도 추가
            if i not in used_indices:
                if change.change_type == ChangeType.INSERTION:
                    pairs.append(
                        ("", change.text, change.paragraph_index, change.author)
                    )
                else:
                    pairs.append(
                        (change.text, "", change.paragraph_index, change.author)
                    )
                used_indices.add(i)

        return pairs

    def _classify_change_pair(
        self,
        feedback_id: int,
        original: str,
        suggested: str,
        para_idx: int,
        author: str,
    ) -> ClassifiedFeedback:
        """삭제+삽입 쌍을 분류합니다."""

        # 분류 점수 계산
        scores = {
            FeedbackType.TERMINOLOGY: 0.0,
            FeedbackType.ERROR: 0.0,
            FeedbackType.STYLE: 0.0,
            FeedbackType.OTHER: 0.0,
        }

        combined_text = f"{original} {suggested}"

        # 패턴 매칭
        for pattern, weight in TERMINOLOGY_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                scores[FeedbackType.TERMINOLOGY] += weight

        for pattern, weight in ERROR_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                scores[FeedbackType.ERROR] += weight

        for pattern, weight in STYLE_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                scores[FeedbackType.STYLE] += weight

        # 단어 수 기반 분류 (짧은 변경은 용어 수정 가능성 높음)
        original_words = len(original.split())
        suggested_words = len(suggested.split())

        if (
            original_words <= WORD_LEVEL_THRESHOLD
            and suggested_words <= WORD_LEVEL_THRESHOLD
        ):
            scores[FeedbackType.TERMINOLOGY] += 0.3

        # 상기 추가/누락 검사
        if "상기" in suggested and "상기" not in original:
            scores[FeedbackType.ERROR] += 0.8

        # 기존 용어집과 비교
        original_lower = original.lower().strip()
        if original_lower in self.existing_terms:
            scores[FeedbackType.TERMINOLOGY] += 0.5

        # 최고 점수 유형 선택
        best_type = max(scores, key=lambda k: scores[k])
        best_score = scores[best_type]

        # 신뢰도가 낮으면 OTHER로 분류
        if best_score < 0.3:
            best_type = FeedbackType.OTHER
            best_score = 0.5

        # 대상 파일 결정
        target_files = self._get_target_files(best_type)

        # 분류 사유 생성
        reason = self._generate_reason(best_type, original, suggested)

        return ClassifiedFeedback(
            id=feedback_id,
            source_type="track_change",
            feedback_type=best_type,
            confidence=min(best_score, 1.0),
            original_text=original,
            suggested_text=suggested,
            context=f"[문단 {para_idx}]",
            classification_reason=reason,
            target_files=target_files,
            author=author,
            paragraph_index=para_idx,
        )

    def _classify_comment(
        self, feedback_id: int, comment: Comment
    ) -> ClassifiedFeedback:
        """코멘트를 분류합니다."""

        scores = {
            FeedbackType.TERMINOLOGY: 0.0,
            FeedbackType.ERROR: 0.0,
            FeedbackType.STYLE: 0.0,
            FeedbackType.OTHER: 0.0,
        }

        text = comment.text

        # 패턴 매칭
        for pattern, weight in TERMINOLOGY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                scores[FeedbackType.TERMINOLOGY] += weight

        for pattern, weight in ERROR_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                scores[FeedbackType.ERROR] += weight

        for pattern, weight in STYLE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                scores[FeedbackType.STYLE] += weight

        # 최고 점수 유형 선택
        best_type = max(scores, key=lambda k: scores[k])
        best_score = scores[best_type]

        # 기본값
        if best_score < 0.3:
            best_type = FeedbackType.STYLE  # 코멘트는 기본적으로 스타일
            best_score = 0.5

        target_files = self._get_target_files(best_type)
        reason = self._generate_comment_reason(best_type, comment)

        # 코멘트에서 수정 제안 추출 시도
        suggested = self._extract_suggestion_from_comment(comment.text)

        return ClassifiedFeedback(
            id=feedback_id,
            source_type="comment",
            feedback_type=best_type,
            confidence=min(best_score, 1.0),
            original_text=comment.target_text,
            suggested_text=suggested,
            context=f"[문단 {comment.paragraph_index}] {comment.text}",
            classification_reason=reason,
            target_files=target_files,
            author=comment.author,
            paragraph_index=comment.paragraph_index,
        )

    def _get_target_files(self, feedback_type: FeedbackType) -> List[str]:
        """피드백 유형에 따른 대상 파일 목록을 반환합니다."""
        if feedback_type == FeedbackType.TERMINOLOGY:
            return ["terminology-db.md", "project-tb.md"]
        elif feedback_type == FeedbackType.ERROR:
            return ["error-patterns.md", "feedback-log.md"]
        elif feedback_type == FeedbackType.STYLE:
            return ["feedback-log.md"]
        else:
            return ["feedback-log.md"]

    def _generate_reason(
        self, feedback_type: FeedbackType, original: str, suggested: str
    ) -> str:
        """분류 사유를 생성합니다."""
        if feedback_type == FeedbackType.TERMINOLOGY:
            if original and suggested:
                return f"용어 대체: '{original[:20]}...' → '{suggested[:20]}...'"
            elif suggested:
                return f"용어 추가: '{suggested[:30]}...'"
            else:
                return f"용어 삭제: '{original[:30]}...'"

        elif feedback_type == FeedbackType.ERROR:
            if "상기" in suggested and "상기" not in original:
                return "상기(antecedent basis) 추가"
            return "오류 수정"

        elif feedback_type == FeedbackType.STYLE:
            return "스타일/표현 개선"

        return "기타 피드백"

    def _generate_comment_reason(
        self, feedback_type: FeedbackType, comment: Comment
    ) -> str:
        """코멘트 분류 사유를 생성합니다."""
        preview = comment.text[:50] + "..." if len(comment.text) > 50 else comment.text
        return f"코멘트: {preview}"

    def _extract_suggestion_from_comment(self, text: str) -> str:
        """코멘트에서 수정 제안을 추출합니다."""
        # "→", "->", "으로", "로 수정" 패턴 찾기
        patterns = [
            r"[→\->]\s*(.+?)(?:\s*$|[.。])",
            r'["\'](.+?)["\'](?:\s*으로|\s*로)',
            r"수정[:\s]+(.+?)(?:\s*$|[.。])",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""


def main() -> int:
    """CLI 엔트리포인트"""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        # 피드백 데이터 로드
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        feedback = DocxFeedback.from_dict(data)

        # 분류 실행
        classifier = FeedbackClassifier()
        classified = classifier.classify_all(feedback)

        # 요약 출력
        print(f"\n=== 피드백 분류 완료 ===")
        print(f"총 항목: {len(classified)}건")

        type_counts = {}
        for cf in classified:
            type_name = cf.feedback_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        for type_name, count in sorted(type_counts.items()):
            print(f"  - {type_name}: {count}건")

        # JSON 출력
        if output_path:
            output_file = Path(output_path)
        else:
            output_file = Path(input_path).with_suffix(".classified.json")

        output_data = {
            "source_file": feedback.source_file,
            "extraction_date": feedback.extraction_date.isoformat(),
            "classified_feedback": [cf.to_dict() for cf in classified],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n출력 파일: {output_file}")

        # 분류 결과 미리보기
        print(f"\n--- 분류 결과 (최대 5건) ---")
        for cf in classified[:5]:
            conf_pct = int(cf.confidence * 100)
            orig_preview = (
                cf.original_text[:20] + "..."
                if len(cf.original_text) > 20
                else cf.original_text
            )
            sugg_preview = (
                cf.suggested_text[:20] + "..."
                if len(cf.suggested_text) > 20
                else cf.suggested_text
            )
            print(
                f'[{cf.id}] {cf.feedback_type.value} ({conf_pct}%): "{orig_preview}" → "{sugg_preview}"'
            )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
