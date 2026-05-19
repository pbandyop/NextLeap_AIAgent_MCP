from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProductConfig:
    product_id: str
    display_name: str
    app_store_id: str
    play_package: str
    doc_title_template: str
    window_weeks: int = 10
    min_reviews_threshold: int = 10
    app_store_country: str = "in"
    play_fetch_count: int = 200
    app_store_max_pages: int = 10
    recipients: list[str] = field(default_factory=list)
    google_doc_id: str = ""


@dataclass
class McpServerConfig:
    name: str
    enabled: bool
    transport: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    base_url: str = ""
    timeout_seconds: int = 60


def resolve_google_doc_id(product: ProductConfig) -> str:
    """
    Per-product Google Doc ID for weekly pulse append.
    Priority: PULSE_DOC_ID_{PRODUCT} env → google_doc_id in products.yaml → GOOGLE_DOC_ID env.
    """
    env_key = f"PULSE_DOC_ID_{product.product_id.upper()}"
    doc_id = os.environ.get(env_key, "").strip()
    if doc_id:
        return doc_id
    if product.google_doc_id.strip():
        return product.google_doc_id.strip()
    fallback = os.environ.get("GOOGLE_DOC_ID", "").strip()
    if fallback:
        return fallback
    raise KeyError(
        f"No Google Doc ID for product {product.product_id!r}. "
        f"Set {env_key} or google_doc_id in config/products.yaml"
    )


def resolve_email_recipient(product: ProductConfig) -> str:
    """
    Stakeholder inbox for weekly pulse email.
    Priority: PULSE_EMAIL_TO_{PRODUCT} → PULSE_EMAIL_TO → first entry in products.yaml recipients.
    """
    env_key = f"PULSE_EMAIL_TO_{product.product_id.upper()}"
    address = os.environ.get(env_key, "").strip()
    if address:
        return address
    global_to = os.environ.get("PULSE_EMAIL_TO", "").strip()
    if global_to:
        return global_to
    if product.recipients:
        return str(product.recipients[0]).strip()
    raise KeyError(
        f"No email recipient for product {product.product_id!r}. "
        f"Set PULSE_EMAIL_TO or {env_key} in .env"
    )


def resolve_email_mode(config: AppConfig) -> str:
    from pulse_agent.phases.phase_07_hardening.gates import effective_email_mode

    return effective_email_mode(config)


@dataclass
class AppConfig:
    products: dict[str, ProductConfig]
    mcp_servers: dict[str, McpServerConfig]
    pulse_env: str = "dev"
    email_mode: str = "draft"
    project_root: Path = field(default_factory=Path.cwd)

    def get_product(self, product_id: str) -> ProductConfig:
        if product_id not in self.products:
            raise KeyError(f"Unknown product_id: {product_id!r}")
        return self.products[product_id]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(project_root: Path | None = None) -> AppConfig:
    root = project_root or Path.cwd()
    config_dir = root / "config"

    products_raw = _load_yaml(config_dir / "products.yaml")
    mcp_raw = _load_yaml(config_dir / "mcp_servers.yaml")

    products: dict[str, ProductConfig] = {}
    for pid, pdata in (products_raw.get("products") or {}).items():
        products[pid] = ProductConfig(
            product_id=pid,
            display_name=str(pdata["display_name"]),
            app_store_id=str(pdata["app_store_id"]),
            play_package=str(pdata["play_package"]),
            doc_title_template=str(pdata.get("doc_title_template", f"Weekly Review Pulse — {pid}")),
            window_weeks=int(pdata.get("window_weeks", 10)),
            min_reviews_threshold=int(pdata.get("min_reviews_threshold", 10)),
            app_store_country=str(pdata.get("app_store_country", "in")),
            play_fetch_count=int(pdata.get("play_fetch_count", 200)),
            app_store_max_pages=int(pdata.get("app_store_max_pages", 10)),
            recipients=list(pdata.get("recipients") or []),
            google_doc_id=str(pdata.get("google_doc_id") or ""),
        )

    mcp_servers: dict[str, McpServerConfig] = {}
    for name, sdata in (mcp_raw.get("servers") or {}).items():
        transport = str(sdata.get("transport", "stdio"))
        mcp_servers[name] = McpServerConfig(
            name=name,
            enabled=bool(sdata.get("enabled", True)),
            transport=transport,
            command=str(sdata.get("command") or ""),
            args=list(sdata.get("args") or []),
            base_url=str(sdata.get("base_url") or ""),
            timeout_seconds=int(sdata.get("timeout_seconds", 60)),
        )

    return AppConfig(
        products=products,
        mcp_servers=mcp_servers,
        pulse_env=os.environ.get("PULSE_ENV", "dev"),
        email_mode=os.environ.get("EMAIL_MODE", "draft"),
        project_root=root,
    )
