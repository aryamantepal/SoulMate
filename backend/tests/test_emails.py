from app.api.emails import _build_html


def test_build_html_escapes_untrusted_fields() -> None:
    html = _build_html(
        [
            {
                "name": "<script>alert(1)</script>",
                "brand": "A&B",
                "url": "https://stockx.com/x?a=1&b='2'",
                "lowest_ask": 100.0,
                "savings": 20.0,
            }
        ]
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "A&amp;B" in html
    assert "href='https://stockx.com/x?a=1&amp;b=&#x27;2&#x27;'" in html


def test_build_html_drops_non_http_links() -> None:
    html = _build_html([{"name": "Shoe", "url": "javascript:alert(1)"}])
    assert "javascript:" not in html
    assert "View on StockX" not in html
