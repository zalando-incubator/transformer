# pylint: skip-file

import io
import os
import logging

from unittest.mock import patch

from transformer.blacklist import on_blacklist, from_file as read_blacklist


class TestBlacklist:
    @patch("builtins.open")
    def test_it_returns_false_and_logs_error_if_the_blacklist_does_not_exist(
        self, mock_open, caplog
    ):
        mock_open.side_effect = FileNotFoundError
        caplog.set_level(logging.DEBUG)
        blacklist = read_blacklist()
        assert len(blacklist) == 0
        assert on_blacklist(blacklist, "whatever") is False
        assert f"Could not read blacklist file {os.getcwd()}/.urlignore" in caplog.text

    @patch("builtins.open")
    def test_it_returns_false_if_the_blacklist_is_empty(self, mock_open):
        mock_open.return_value = io.StringIO("")
        assert on_blacklist(read_blacklist(), "") is False

    @patch("builtins.open")
    def test_it_returns_false_if_url_is_not_on_blacklist(self, mock_open):
        mock_open.return_value = io.StringIO("www.amazon.com")
        assert on_blacklist(read_blacklist(), "www.zalando.de") is False

    @patch("builtins.open")
    def test_it_returns_true_if_url_is_on_blacklist(self, mock_open):
        mock_open.return_value = io.StringIO("www.google.com\nwww.amazon.com")
        assert on_blacklist(read_blacklist(), "www.amazon.com") is True

    @patch("builtins.open")
    def test_it_returns_true_if_a_partial_match_is_found(self, mock_open):
        mock_open.return_value = io.StringIO("www.amazon.com")
        assert on_blacklist(read_blacklist(), "http://www.amazon.com/") is True

    @patch("builtins.open")
    def test_it_ignores_whitespace_only_lines(self, mock_open):
        mock_open.return_value = io.StringIO(" \n   \r\nwww.amazon.com")
        assert on_blacklist(read_blacklist(), "www.zalando.de") is False

    @patch("builtins.open")
    def test_it_removes_duplicate_entries(self, mock_open):
        mock_open.return_value = io.StringIO("\nwww.amazon.com" * 3)
        assert len(read_blacklist()) == 1
