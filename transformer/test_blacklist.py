# pylint: skip-file

import io
import os
import logging

from unittest.mock import patch

from transformer.blacklist import on_blacklist


class TestBlacklist:
    @patch("builtins.open")
    def test_it_returns_false_and_logs_error_if_the_blacklist_does_not_exist(
        self, mock_open, caplog
    ):
        mock_open.side_effect = FileNotFoundError
        caplog.set_level(logging.DEBUG)
        assert on_blacklist("") is False
        assert f"Could not read blacklist file {os.getcwd()}/.urlignore" in caplog.text

    @patch("builtins.open")
    def test_it_returns_false_if_the_blacklist_is_empty(self, mock_open):
        mock_open.return_value = io.StringIO("")
        assert on_blacklist("") is False

    @patch("builtins.open")
    def test_it_returns_false_if_url_is_not_on_blacklist(self, mock_open):
        mock_open.return_value = io.StringIO("www.amazon.com")
        assert on_blacklist("www.zalando.de") is False

    @patch("builtins.open")
    def test_it_returns_true_if_url_is_on_blacklist(self, mock_open):
        mock_open.return_value = io.StringIO("www.google.com\nwww.amazon.com")
        assert on_blacklist("www.amazon.com") is True

    @patch("builtins.open")
    def test_it_returns_true_if_a_partial_match_is_found(self, mock_open):
        mock_open.return_value = io.StringIO("www.amazon.com")
        assert on_blacklist("http://www.amazon.com/") is True

    @patch("builtins.open")
    def test_it_ignores_empty_lines(self, mock_open):
        mock_open.return_value = io.StringIO("\nwww.amazon.com")
        assert on_blacklist("www.zalando.de") is False
