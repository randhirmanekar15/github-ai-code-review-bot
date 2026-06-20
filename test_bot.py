"""Tests for pure helpers (no GitHub / model required)."""

from bot import build_review_prompt, format_comment


def test_build_review_prompt_includes_filename_and_patch():
    prompt = build_review_prompt("auth.py", "@@ -1 +1 @@\n-old\n+new")
    assert "auth.py" in prompt
    assert "+new" in prompt


def test_format_comment_is_markdown():
    body = format_comment("utils.py", "Looks good.")
    assert body.startswith("### AI review")
    assert "`utils.py`" in body
    assert "Looks good." in body
