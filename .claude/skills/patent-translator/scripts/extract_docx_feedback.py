#!/usr/bin/env python3
"""
Word Track Changes 및 Comments 추출기

.docx 파일에서 Track Changes(삽입/삭제)와 Comments를 추출합니다.
python-docx는 revision 접근이 제한적이므로 zipfile + lxml 방식을 사용합니다.

사용법:
    python extract_docx_feedback.py <input.docx> [output.json]

예시:
    python extract_docx_feedback.py translation-reviewed.docx
    python extract_docx_feedback.py translation-reviewed.docx feedback-data.json
"""

import sys
import os
import zipfile
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

# 현재 스크립트 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from lxml import etree  # type: ignore
except ImportError:
    print("Error: lxml 패키지가 필요합니다.")
    print("설치: pip install lxml")
    sys.exit(1)

from feedback_models import (  # type: ignore
    TrackChange,
    Comment,
    DocxFeedback,
    ChangeType,
)


# Word OOXML 네임스페이스
NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


class DocxFeedbackExtractor:
    """Word 문서에서 Track Changes와 Comments를 추출하는 클래스"""

    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path)
        if not self.docx_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {docx_path}")
        if not self.docx_path.suffix.lower() == ".docx":
            raise ValueError(f"지원하지 않는 파일 형식입니다: {self.docx_path.suffix}")

        self._zip_file: Any = None
        self._document_tree: Any = None
        self._comments_tree: Any = None
        self._paragraphs: List[Any] = []
        self._paragraph_texts: List[str] = []

    def extract(self) -> DocxFeedback:
        """모든 피드백 데이터를 추출합니다."""
        with zipfile.ZipFile(self.docx_path, "r") as zf:
            self._zip_file = zf
            self._load_document()
            self._load_comments()
            self._build_paragraph_index()

            track_changes = self._extract_track_changes()
            comments = self._extract_comments()

        return DocxFeedback(
            source_file=str(self.docx_path),
            extraction_date=datetime.now(),
            track_changes=track_changes,
            comments=comments,
        )

    def _load_document(self) -> None:
        """word/document.xml을 로드합니다."""
        try:
            with self._zip_file.open("word/document.xml") as f:
                self._document_tree = etree.parse(f).getroot()
        except KeyError:
            raise ValueError("유효한 .docx 파일이 아닙니다: word/document.xml 없음")

    def _load_comments(self) -> None:
        """word/comments.xml을 로드합니다 (없으면 None)."""
        try:
            with self._zip_file.open("word/comments.xml") as f:
                self._comments_tree = etree.parse(f).getroot()
        except KeyError:
            self._comments_tree = None  # 코멘트가 없는 문서

    def _build_paragraph_index(self) -> None:
        """문단 인덱스를 구축합니다 (컨텍스트 추출용)."""
        body = self._document_tree.find(".//w:body", NAMESPACES)
        if body is None:
            return

        self._paragraphs = body.findall(".//w:p", NAMESPACES)
        for p in self._paragraphs:
            # 문단의 전체 텍스트 추출 (Track Changes 포함)
            text_parts = []
            for t in p.iter("{%s}t" % NAMESPACES["w"]):
                if t.text:
                    text_parts.append(t.text)
            for dt in p.iter("{%s}delText" % NAMESPACES["w"]):
                if dt.text:
                    text_parts.append(f"[DEL:{dt.text}]")
            self._paragraph_texts.append("".join(text_parts))

    def _get_paragraph_index(self, element: Any) -> int:
        """요소가 속한 문단의 인덱스를 반환합니다."""
        # 부모 문단 찾기
        parent = element
        while parent is not None:
            if parent.tag == "{%s}p" % NAMESPACES["w"]:
                try:
                    return self._paragraphs.index(parent)
                except ValueError:
                    return -1
            parent = parent.getparent()
        return -1

    def _get_context(
        self, paragraph_index: int, max_chars: int = 50
    ) -> Tuple[str, str]:
        """문단 주변 컨텍스트를 반환합니다."""
        context_before = ""
        context_after = ""

        if paragraph_index > 0:
            prev_text = self._paragraph_texts[paragraph_index - 1]
            context_before = (
                prev_text[-max_chars:] if len(prev_text) > max_chars else prev_text
            )

        if paragraph_index < len(self._paragraph_texts) - 1:
            next_text = self._paragraph_texts[paragraph_index + 1]
            context_after = (
                next_text[:max_chars] if len(next_text) > max_chars else next_text
            )

        return context_before, context_after

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Word 날짜 문자열을 datetime으로 변환합니다."""
        if not date_str:
            return None
        try:
            # ISO 8601 형식: 2024-01-15T10:30:00Z
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                # 다른 형식 시도
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return None

    def _extract_track_changes(self) -> List[TrackChange]:
        """모든 Track Changes (삽입/삭제)를 추출합니다."""
        changes: List[TrackChange] = []

        # 삽입 (w:ins) 추출
        for ins in self._document_tree.iter("{%s}ins" % NAMESPACES["w"]):
            text_parts = []
            for t in ins.iter("{%s}t" % NAMESPACES["w"]):
                if t.text:
                    text_parts.append(t.text)

            if not text_parts:
                continue

            text = "".join(text_parts)
            author = ins.get("{%s}author" % NAMESPACES["w"], "Unknown")
            date_str = ins.get("{%s}date" % NAMESPACES["w"])
            xml_id = ins.get("{%s}id" % NAMESPACES["w"])

            para_idx = self._get_paragraph_index(ins)
            context_before, context_after = self._get_context(para_idx)

            changes.append(
                TrackChange(
                    change_type=ChangeType.INSERTION,
                    text=text,
                    author=author,
                    date=self._parse_datetime(date_str),
                    context_before=context_before,
                    context_after=context_after,
                    paragraph_index=para_idx,
                    xml_id=xml_id,
                )
            )

        # 삭제 (w:del) 추출
        for del_elem in self._document_tree.iter("{%s}del" % NAMESPACES["w"]):
            text_parts = []
            for dt in del_elem.iter("{%s}delText" % NAMESPACES["w"]):
                if dt.text:
                    text_parts.append(dt.text)

            if not text_parts:
                continue

            text = "".join(text_parts)
            author = del_elem.get("{%s}author" % NAMESPACES["w"], "Unknown")
            date_str = del_elem.get("{%s}date" % NAMESPACES["w"])
            xml_id = del_elem.get("{%s}id" % NAMESPACES["w"])

            para_idx = self._get_paragraph_index(del_elem)
            context_before, context_after = self._get_context(para_idx)

            changes.append(
                TrackChange(
                    change_type=ChangeType.DELETION,
                    text=text,
                    author=author,
                    date=self._parse_datetime(date_str),
                    context_before=context_before,
                    context_after=context_after,
                    paragraph_index=para_idx,
                    xml_id=xml_id,
                )
            )

        # 문단 순서로 정렬
        changes.sort(key=lambda c: (c.paragraph_index, c.date or datetime.min))

        return changes

    def _extract_comments(self) -> List[Comment]:
        """모든 Comments를 추출합니다."""
        if self._comments_tree is None:
            return []

        comments: List[Comment] = []

        # 코멘트 범위 맵 구축 (comment ID -> target text)
        comment_ranges = self._build_comment_ranges()

        # 코멘트 추출
        for comment_elem in self._comments_tree.iter("{%s}comment" % NAMESPACES["w"]):
            comment_id_str = comment_elem.get("{%s}id" % NAMESPACES["w"])
            if not comment_id_str:
                continue

            try:
                comment_id = int(comment_id_str)
            except ValueError:
                continue

            # 코멘트 텍스트 추출
            text_parts = []
            for t in comment_elem.iter("{%s}t" % NAMESPACES["w"]):
                if t.text:
                    text_parts.append(t.text)

            comment_text = "".join(text_parts)
            if not comment_text.strip():
                continue

            author = comment_elem.get("{%s}author" % NAMESPACES["w"], "Unknown")
            date_str = comment_elem.get("{%s}date" % NAMESPACES["w"])

            # 대상 텍스트 및 문단 인덱스
            target_text, para_idx = comment_ranges.get(comment_id, ("", -1))

            comments.append(
                Comment(
                    comment_id=comment_id,
                    author=author,
                    date=self._parse_datetime(date_str),
                    text=comment_text,
                    target_text=target_text,
                    paragraph_index=para_idx,
                    replied_to=None,  # 답글 처리는 추후 구현
                )
            )

        # ID 순서로 정렬
        comments.sort(key=lambda c: c.comment_id)

        return comments

    def _build_comment_ranges(self) -> Dict[int, Tuple[str, int]]:
        """코멘트 ID를 대상 텍스트와 문단 인덱스에 매핑합니다."""
        ranges: Dict[int, Tuple[str, int]] = {}

        # commentRangeStart와 commentRangeEnd 사이의 텍스트 수집
        for start in self._document_tree.iter(
            "{%s}commentRangeStart" % NAMESPACES["w"]
        ):
            comment_id_str = start.get("{%s}id" % NAMESPACES["w"])
            if not comment_id_str:
                continue

            try:
                comment_id = int(comment_id_str)
            except ValueError:
                continue

            # 범위 내 텍스트 수집 (간소화된 방식)
            # 실제로는 start와 end 사이의 모든 w:t를 수집해야 하지만,
            # 복잡도를 줄이기 위해 같은 문단 내 텍스트만 수집
            para_idx = self._get_paragraph_index(start)
            if para_idx >= 0 and para_idx < len(self._paragraph_texts):
                target_text = self._paragraph_texts[para_idx]
                # Track Changes 마커 제거
                target_text = re.sub(r"\[DEL:.*?\]", "", target_text)
                ranges[comment_id] = (target_text[:100], para_idx)  # 최대 100자

        return ranges


def main() -> int:
    """CLI 엔트리포인트"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    docx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        extractor = DocxFeedbackExtractor(docx_path)
        feedback = extractor.extract()

        # 요약 출력
        print(f"\n=== Track Changes & Comments 추출 완료 ===")
        print(f"소스 파일: {feedback.source_file}")
        print(f"추출 일시: {feedback.extraction_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"총 항목: {feedback.total_items}건")
        print(f"  - 삽입: {feedback.insertion_count}건")
        print(f"  - 삭제: {feedback.deletion_count}건")
        print(f"  - 코멘트: {len(feedback.comments)}건")

        # JSON 출력
        if output_path:
            output_file = Path(output_path)
        else:
            output_file = Path(docx_path).with_suffix(".feedback.json")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(feedback.to_json())

        print(f"\n출력 파일: {output_file}")

        # 상세 내용 미리보기
        if feedback.track_changes:
            print(f"\n--- Track Changes (최대 5건) ---")
            for i, tc in enumerate(feedback.track_changes[:5]):
                change_type = (
                    "삽입" if tc.change_type == ChangeType.INSERTION else "삭제"
                )
                text_preview = tc.text[:50] + "..." if len(tc.text) > 50 else tc.text
                print(f'[{i + 1}] {change_type}: "{text_preview}" (by {tc.author})')

        if feedback.comments:
            print(f"\n--- Comments (최대 5건) ---")
            for i, c in enumerate(feedback.comments[:5]):
                text_preview = c.text[:50] + "..." if len(c.text) > 50 else c.text
                target_preview = (
                    c.target_text[:30] + "..."
                    if len(c.target_text) > 30
                    else c.target_text
                )
                print(
                    f'[{i + 1}] "{text_preview}" -> "{target_preview}" (by {c.author})'
                )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
