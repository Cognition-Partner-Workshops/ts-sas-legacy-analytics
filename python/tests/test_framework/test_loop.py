"""
Tests for sas_utils.framework.loop

Derived from Macro/loop.sas Usage block (lines 52-184).
"""

import pytest

from sas_utils.framework.loop import loop


# ====================================================================
# Test: simple loop with callback
# From: %loop(Hello World) with %put &word
# ====================================================================
class TestSimpleLoop:
    def test_space_separated_words(self):
        collected = []
        loop("Hello World", lambda w: collected.append(w))
        assert collected == ["Hello", "World"]

    def test_callback_return_values(self):
        results = loop("Hello World", lambda w: w.upper())
        assert results == ["HELLO", "WORLD"]

    def test_single_word(self):
        collected = []
        loop("Hello", lambda w: collected.append(w))
        assert collected == ["Hello"]


# ====================================================================
# Test: loop with custom delimiter
# From: items separated by comma
# ====================================================================
class TestCustomDelimiter:
    def test_comma_delimiter(self):
        collected = []
        loop("Hello,World", lambda w: collected.append(w), dlm=",")
        assert collected == ["Hello", "World"]

    def test_pipe_delimiter(self):
        collected = []
        loop("A|B|C", lambda w: collected.append(w), dlm="|")
        assert collected == ["A", "B", "C"]


# ====================================================================
# Test: loop with list input
# ====================================================================
class TestListInput:
    def test_list_input(self):
        collected = []
        loop(["Hello", "World"], lambda w: collected.append(w))
        assert collected == ["Hello", "World"]

    def test_empty_list(self):
        collected = []
        loop([], lambda w: collected.append(w))
        assert collected == []


# ====================================================================
# Test: nested loop calls
# From: nested %loop invocations
# ====================================================================
class TestNestedLoops:
    def test_nested_loops(self):
        outer_items = []
        inner_items = []

        def outer_callback(word):
            outer_items.append(word)
            loop("X Y", lambda w: inner_items.append(f"{word}-{w}"))

        loop("A B", outer_callback)

        assert outer_items == ["A", "B"]
        assert inner_items == ["A-X", "A-Y", "B-X", "B-Y"]


# ====================================================================
# Test: empty string input
# ====================================================================
class TestEdgeCases:
    def test_empty_string(self):
        collected = []
        loop("", lambda w: collected.append(w))
        assert collected == []

    def test_multiple_spaces(self):
        collected = []
        loop("A  B  C", lambda w: collected.append(w))
        assert collected == ["A", "B", "C"]
