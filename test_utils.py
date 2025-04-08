import pytest
from utils import fetch_url_content

def test_fetch_url_content_valid_url():
    assert fetch_url_content("https://example.com") is not None

def test_fetch_url_content_invalid_url():
    with pytest.raises(ValueError):
        fetch_url_content("invalid-url")
