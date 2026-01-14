#!/usr/bin/env python3
"""
Word Track Changes 피드백 시스템 데이터 모델

특허번역 검토 워크플로우에서 사용되는 공통 데이터 클래스를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import json


class ChangeType(Enum):
    """Track Change 유형"""

    INSERTION = "insertion"
    DELETION = "deletion"


class FeedbackType(Enum):
    """피드백 분류 유형"""

    TERMINOLOGY = "terminology"  # 용어 수정
    ERROR = "error"  # 오류 수정 (상기 누락 등)
    STYLE = "style"  # 스타일/표현 개선
    OTHER = "other"  # 기타


@dataclass
class TrackChange:
    """Word Track Change (삽입/삭제) 데이터"""

    change_type: ChangeType
    text: str
    author: str
    date: Optional[datetime]
    context_before: str  # 변경 전후 문맥 (~50자)
    context_after: str
    paragraph_index: int
    xml_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "text": self.text,
            "author": self.author,
            "date": self.date.isoformat() if self.date else None,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "paragraph_index": self.paragraph_index,
            "xml_id": self.xml_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackChange":
        return cls(
            change_type=ChangeType(data["change_type"]),
            text=data["text"],
            author=data["author"],
            date=datetime.fromisoformat(data["date"]) if data.get("date") else None,
            context_before=data["context_before"],
            context_after=data["context_after"],
            paragraph_index=data["paragraph_index"],
            xml_id=data.get("xml_id"),
        )


@dataclass
class Comment:
    """Word 코멘트 데이터"""

    comment_id: int
    author: str
    date: Optional[datetime]
    text: str  # 코멘트 내용
    target_text: str  # 코멘트가 달린 본문 텍스트
    paragraph_index: int
    replied_to: Optional[int] = None  # 답글인 경우 부모 코멘트 ID

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "author": self.author,
            "date": self.date.isoformat() if self.date else None,
            "text": self.text,
            "target_text": self.target_text,
            "paragraph_index": self.paragraph_index,
            "replied_to": self.replied_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        return cls(
            comment_id=data["comment_id"],
            author=data["author"],
            date=datetime.fromisoformat(data["date"]) if data.get("date") else None,
            text=data["text"],
            target_text=data["target_text"],
            paragraph_index=data["paragraph_index"],
            replied_to=data.get("replied_to"),
        )


@dataclass
class ClassifiedFeedback:
    """분류된 피드백 항목"""

    id: int
    source_type: str  # 'track_change' | 'comment'
    feedback_type: FeedbackType
    confidence: float  # 0.0 ~ 1.0 (분류 신뢰도)
    original_text: str  # 변경 전 텍스트 (삭제된 텍스트 또는 코멘트 대상)
    suggested_text: str  # 변경 후 텍스트 (삽입된 텍스트)
    context: str  # 주변 문맥
    classification_reason: str  # 분류 사유
    target_files: List[str]  # 반영 대상 파일 목록
    author: str = ""
    paragraph_index: int = 0
    approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "feedback_type": self.feedback_type.value,
            "confidence": self.confidence,
            "original_text": self.original_text,
            "suggested_text": self.suggested_text,
            "context": self.context,
            "classification_reason": self.classification_reason,
            "target_files": self.target_files,
            "author": self.author,
            "paragraph_index": self.paragraph_index,
            "approved": self.approved,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClassifiedFeedback":
        return cls(
            id=data["id"],
            source_type=data["source_type"],
            feedback_type=FeedbackType(data["feedback_type"]),
            confidence=data["confidence"],
            original_text=data["original_text"],
            suggested_text=data["suggested_text"],
            context=data["context"],
            classification_reason=data["classification_reason"],
            target_files=data["target_files"],
            author=data.get("author", ""),
            paragraph_index=data.get("paragraph_index", 0),
            approved=data.get("approved", False),
        )


@dataclass
class DocxFeedback:
    """DOCX에서 추출한 전체 피드백 컨테이너"""

    source_file: str
    extraction_date: datetime
    track_changes: List[TrackChange] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return len(self.track_changes) + len(self.comments)

    @property
    def insertion_count(self) -> int:
        return sum(
            1 for tc in self.track_changes if tc.change_type == ChangeType.INSERTION
        )

    @property
    def deletion_count(self) -> int:
        return sum(
            1 for tc in self.track_changes if tc.change_type == ChangeType.DELETION
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_file": self.source_file,
            "extraction_date": self.extraction_date.isoformat(),
            "track_changes": [tc.to_dict() for tc in self.track_changes],
            "comments": [c.to_dict() for c in self.comments],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocxFeedback":
        return cls(
            source_file=data["source_file"],
            extraction_date=datetime.fromisoformat(data["extraction_date"]),
            track_changes=[
                TrackChange.from_dict(tc) for tc in data.get("track_changes", [])
            ],
            comments=[Comment.from_dict(c) for c in data.get("comments", [])],
        )

    @classmethod
    def from_json(cls, json_str: str) -> "DocxFeedback":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ApplyResult:
    """피드백 적용 결과"""

    terminology_added: int = 0
    terminology_updated: int = 0
    errors_added: int = 0
    styles_logged: int = 0
    project_tb_updated: int = 0
    failures: List[str] = field(default_factory=list)

    @property
    def total_applied(self) -> int:
        return (
            self.terminology_added
            + self.terminology_updated
            + self.errors_added
            + self.styles_logged
        )

    @property
    def success(self) -> bool:
        return len(self.failures) == 0

    def to_summary(self) -> str:
        lines = [
            f"적용 완료: {self.total_applied}건",
            f"  - 용어 추가: {self.terminology_added}건",
            f"  - 용어 수정: {self.terminology_updated}건",
            f"  - 오류 패턴: {self.errors_added}건",
            f"  - 스타일 로그: {self.styles_logged}건",
            f"  - 프로젝트 TB: {self.project_tb_updated}건",
        ]
        if self.failures:
            lines.append(f"실패: {len(self.failures)}건")
            for f in self.failures[:5]:  # 최대 5건만 표시
                lines.append(f"  - {f}")
        return "\n".join(lines)
