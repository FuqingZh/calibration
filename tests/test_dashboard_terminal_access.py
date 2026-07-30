from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
NGINX_CONFIG = (
    REPOSITORY_ROOT / "docs/runbooks/artifacts/ao-dashboard-readonly.nginx.conf"
).read_text(encoding="utf-8")


def _location_block(pattern: str) -> str:
    match = re.search(
        rf"location {re.escape(pattern)} \{{(?P<body>.*?)^\s{{8}}\}}",
        NGINX_CONFIG,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def test_exact_mux_route_has_only_the_two_authorized_clients() -> None:
    mux = _location_block("= /mux")

    assert re.findall(r"^\s*allow ([^;]+);", mux, flags=re.MULTILINE) == [
        "192.168.30.134",
        "192.168.30.205",
    ]
    assert re.findall(r"^\s*deny ([^;]+);", mux, flags=re.MULTILINE) == [
        "all",
        "all",
    ]
    assert "allow 192.168.30.0/24;" not in mux
    assert "proxy_pass http://127.0.0.1:3001/mux;" in mux
    assert "proxy_set_header Upgrade $http_upgrade;" in mux
    assert 'proxy_set_header Connection "upgrade";' in mux
    assert "proxy_connect_timeout 2s;" in mux
    assert "proxy_send_timeout 1h;" in mux
    assert re.search(
        r"limit_except GET \{\s*deny all;\s*\}",
        mux,
        flags=re.DOTALL,
    )
    assert "location /mux" not in NGINX_CONFIG


def test_dashboard_and_api_keep_the_shared_read_only_boundary() -> None:
    assert "allow 192.168.30.0/24;" in NGINX_CONFIG

    for pattern in ("= /dashboard-health", "/api/", "/"):
        location = _location_block(pattern)
        assert "allow 192.168.30.0/24;" in location
        assert "deny all;" in location
        assert re.search(
            r"limit_except GET \{\s*deny all;\s*\}",
            location,
            flags=re.DOTALL,
        )


def test_terminal_access_does_not_add_mutation_or_shell_routes() -> None:
    assert NGINX_CONFIG.count("proxy_pass http://127.0.0.1:3001/mux;") == 1
    assert not re.search(r"location [^{]*(shell|terminal)", NGINX_CONFIG)
