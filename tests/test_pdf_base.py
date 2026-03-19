"""Tests for pdf/base.py — BasePdfGenerator utilities."""

from datetime import date

from ws_contracts.pdf.base import BasePdfGenerator


class TestFormatDate:

    def test_date_object(self):
        assert BasePdfGenerator.format_date(date(2025, 1, 15)) == "January 15, 2025"

    def test_iso_string(self):
        assert BasePdfGenerator.format_date("2025-02-01") == "February 1, 2025"

    def test_none(self):
        assert BasePdfGenerator.format_date(None) == ""

    def test_invalid_string(self):
        assert BasePdfGenerator.format_date("not-a-date") == "not-a-date"


class TestNumberToWords:

    def test_zero(self):
        assert BasePdfGenerator.number_to_words(0) == "zero"

    def test_single_digit(self):
        assert BasePdfGenerator.number_to_words(5) == "five"

    def test_teens(self):
        assert BasePdfGenerator.number_to_words(13) == "thirteen"

    def test_tens(self):
        assert BasePdfGenerator.number_to_words(42) == "forty two"

    def test_hundred(self):
        assert BasePdfGenerator.number_to_words(100) == "one hundred"

    def test_hundreds_with_remainder(self):
        assert BasePdfGenerator.number_to_words(350) == "three hundred fifty"

    def test_thousands(self):
        assert BasePdfGenerator.number_to_words(3000) == "three thousand"

    def test_complex(self):
        assert BasePdfGenerator.number_to_words(3180) == "three thousand one hundred eighty"
