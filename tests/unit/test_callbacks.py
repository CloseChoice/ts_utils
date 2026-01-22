"""
Unit tests for Dash callbacks.
"""

import pytest

from ts_utils.visualization.callbacks import parse_time_input


def test_parse_time_input_valid_format():
    """Test parsing a valid time input string."""
    result, error = parse_time_input('2024-01-15 14:30:00', None)

    assert result == '2024-01-15 14:30:00'
    assert error is None


def test_parse_time_input_empty_returns_default():
    """Test that empty input returns the default value."""
    result, error = parse_time_input('', '2024-01-01 00:00:00')

    assert result == '2024-01-01 00:00:00'
    assert error is None


def test_parse_time_input_none_returns_default():
    """Test that None input returns the default value."""
    result, error = parse_time_input(None, '2024-12-31 23:59:59')

    assert result == '2024-12-31 23:59:59'
    assert error is None


def test_parse_time_input_whitespace_only_returns_default():
    """Test that whitespace-only input returns the default value."""
    result, error = parse_time_input('   ', '2024-06-15 12:00:00')

    assert result == '2024-06-15 12:00:00'
    assert error is None


def test_parse_time_input_invalid_format_returns_error():
    """Test that invalid format returns error message."""
    result, error = parse_time_input('2024/01/15', None)

    assert result is None
    assert error is not None
    assert 'Invalid format' in error
    assert 'YYYY-MM-DD' in error


def test_parse_time_input_date_only_format():
    """Test that date-only format is accepted and time is appended."""
    result, error = parse_time_input('2024-01-15', None)

    assert result == '2024-01-15 00:00:00'
    assert error is None


def test_parse_time_input_strips_whitespace():
    """Test that input is stripped of leading/trailing whitespace."""
    result, error = parse_time_input('  2024-01-15 14:30:00  ', None)

    assert result == '2024-01-15 14:30:00'
    assert error is None


def test_parse_time_input_invalid_date():
    """Test that invalid date values return error."""
    result, error = parse_time_input('2024-13-45 25:99:99', None)

    assert result is None
    assert error is not None
    assert 'Invalid format' in error


def test_parse_time_input_midnight():
    """Test parsing midnight timestamp."""
    result, error = parse_time_input('2024-01-01 00:00:00', None)

    assert result == '2024-01-01 00:00:00'
    assert error is None


def test_parse_time_input_end_of_day():
    """Test parsing end of day timestamp."""
    result, error = parse_time_input('2024-12-31 23:59:59', None)

    assert result == '2024-12-31 23:59:59'
    assert error is None
