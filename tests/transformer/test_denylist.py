# pylint: skip-file

import io
import os
import logging

from transformer.denylist import on_denylist, from_file as read_denylist


class TestDenylist:

    def test_it_returns_false_and_logs_error_if_the_denylist_does_not_exist(
        self, mock_open, caplog
    ):
        mock_open.side_effect = FileNotFoundError
        caplog.set_level(logging.DEBUG)
        denylist = read_denylist()
        assert len(denylist) == 0
        assert on_denylist(denylist, "whatever") is False
        assert f"Could not read denylist file {os.getcwd()}/.urlignore" in caplog.text

    def test_it_returns_false_if_the_denylist_is_empty(self, mock_open):
        mock_open.return_value = io.StringIO("")
        assert on_denylist(read_denylist(), "") is False

    def test_it_returns_false_if_url_is_not_on_denylist(self, mock_open):
        mock_open.return_value = io.StringIO("www.amazon.com")
        assert on_denylist(read_denylist(), "www.zalando.de") is False

    def test_it_returns_true_if_url_is_on_denylist(self, mock_open):
        mock_open.return_value = io.StringIO("www.google.com\nwww.amazon.com")
        assert on_denylist(read_denylist(), "www.amazon.com") is True

    def test_it_returns_true_if_a_partial_match_is_found(self, mock_open):
        mock_open.return_value = io.StringIO("www.amazon.com")
        assert on_denylist(read_denylist(), "http://www.amazon.com/") is True

    def test_it_ignores_whitespace_only_lines(self, mock_open):
        mock_open.return_value = io.StringIO(" \n   \r\nwww.amazon.com")
        assert on_denylist(read_denylist(), "www.zalando.de") is False

    def test_it_removes_duplicate_entries(self, mock_open):
        mock_open.return_value = io.StringIO("\nwww.amazon.com" * 3)
        assert len(read_denylist()) == 1
