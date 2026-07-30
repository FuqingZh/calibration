from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEPLOYED_NGINX_PATH = (
    REPOSITORY_ROOT / "docs/runbooks/artifacts/ao-dashboard-readonly.nginx.conf"
)
DEPLOYED_SERVICE_PATH = (
    REPOSITORY_ROOT / "docs/runbooks/artifacts/ao-dashboard-readonly.service"
)
PROPOSED_NGINX_CONFIG = (
    REPOSITORY_ROOT
    / "docs/runbooks/artifacts/ao-dashboard-terminal-proposed.nginx.conf"
).read_text(encoding="utf-8")


def _location_block(config: str, pattern: str) -> str:
    match = re.search(
        rf"location {re.escape(pattern)} \{{(?P<body>.*?)^\s{{8}}\}}",
        config,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def test_deployed_artifacts_remain_byte_compatible() -> None:
    assert hashlib.sha256(DEPLOYED_NGINX_PATH.read_bytes()).hexdigest() == (
        "64bc48aa29a11ebc01cfbc8f12b975e3744e0a4c1fe71443cd06ac23caffc3ea"
    )
    assert hashlib.sha256(DEPLOYED_SERVICE_PATH.read_bytes()).hexdigest() == (
        "256ffa02671c5f76a9cce6d5f86827de9236ae46ee53aadeddcaf7ec1d8df1d4"
    )
    deployed = DEPLOYED_NGINX_PATH.read_text(encoding="utf-8")
    mux = _location_block(deployed, "/mux")
    assert "return 404;" in mux
    assert "proxy_pass" not in mux


def test_exact_mux_route_has_only_the_two_authorized_clients() -> None:
    mux = _location_block(PROPOSED_NGINX_CONFIG, "= /mux")

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
    assert "location /mux" not in PROPOSED_NGINX_CONFIG


def test_dashboard_and_api_keep_the_shared_read_only_boundary() -> None:
    assert "allow 192.168.30.0/24;" in PROPOSED_NGINX_CONFIG

    for pattern in ("= /dashboard-health", "/api/", "/"):
        location = _location_block(PROPOSED_NGINX_CONFIG, pattern)
        assert "allow 192.168.30.0/24;" in location
        assert "deny all;" in location
        assert re.search(
            r"limit_except GET \{\s*deny all;\s*\}",
            location,
            flags=re.DOTALL,
        )


def test_terminal_access_does_not_add_mutation_or_shell_routes() -> None:
    assert PROPOSED_NGINX_CONFIG.count("proxy_pass http://127.0.0.1:3001/mux;") == 1
    assert not re.search(r"location [^{]*(shell|terminal)", PROPOSED_NGINX_CONFIG)
