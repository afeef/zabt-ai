# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from unittest.mock import patch


def test_transliterate_urdu_arabic_to_roman_calls_llm():
    from app.services.languages.transliteration import transliterate

    with patch(
        "app.services.languages.transliteration._call_llm"
    ) as mock_llm:
        mock_llm.return_value = "yeh urdu hai"
        out = transliterate(
            text="یہ اردو ہے",
            source_code="urdu_arabic",
            target_code="urdu_roman",
        )

    assert out == "yeh urdu hai"
    args, kwargs = mock_llm.call_args
    assert "Urdu" in args[0]
    assert "Roman" in args[0]


def test_transliterate_returns_empty_string_for_empty_input():
    from app.services.languages.transliteration import transliterate
    assert transliterate(text="", source_code="urdu_arabic", target_code="urdu_roman") == ""
    assert transliterate(text="   ", source_code="urdu_arabic", target_code="urdu_roman") == ""
