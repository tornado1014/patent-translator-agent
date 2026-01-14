#!/bin/bash
# Skill Forced Evaluation Hook
# 3-step commitment mechanism for reliable skill activation (84% success rate)
# Reference: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

cat << 'EOF'
[SKILL ACTIVATION PROTOCOL]

You have available skills. Before proceeding, complete these steps IN ORDER:

## Step 1 - EVALUATE
For the patent-translator skill, evaluate if it applies to this prompt:
- Skill: patent-translator
- Triggers: patent translation, specification translation, claims translation,
  En-Ko technical document localization, 특허 번역, 영한 번역, 명세서 번역,
  translate patent, 번역 시작, 특허문서 번역
- Answer: YES/NO with brief reason

## Step 2 - ACTIVATE
If any skill evaluated as YES, use the Skill() tool NOW to activate it.
DO NOT skip this step. DO NOT proceed without activation.

## Step 3 - IMPLEMENT
Only after Step 2 activation, proceed with the task.

CRITICAL: The evaluation in Step 1 is WORTHLESS unless you complete Step 2.
If you skip activation, you are violating the workflow.
EOF
