#!/bin/bash
# PreToolUse 훅: 섹션 파일 직접 병합 차단
#
# 이 훅은 Bash에서 cat으로 section 파일을 직접 합치려는 시도를 감지하고 차단합니다.
# 한국 특허 표준 섹션 순서를 보장하기 위해 merge-sections.py 사용을 강제합니다.

COMMAND="$1"

# cat + section + .md + 리다이렉션 조합 감지
if echo "$COMMAND" | grep -qE 'cat.*section.*\.md.*>'; then
  echo ""
  echo "┌─────────────────────────────────────────────────────────────┐"
  echo "│  [MERGE_BLOCKED] 섹션 파일 직접 병합이 감지되었습니다.     │"
  echo "└─────────────────────────────────────────────────────────────┘"
  echo ""
  echo "올바른 방법:"
  echo "  python .claude/skills/patent-translator/scripts/merge-sections.py output/[project] --json"
  echo ""
  echo "이 규칙은 한국 특허 표준 섹션 순서를 보장합니다:"
  echo "  발명의 명칭 → 기술분야 → 배경기술 → 도면 → 상세설명 → 청구범위 → 요약서"
  echo ""
  exit 1
fi

exit 0
