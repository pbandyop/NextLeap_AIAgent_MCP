from pulse_agent.config.loader import load_config


def test_config_loads_products_and_mcp(project_root):
    config = load_config(project_root)
    assert "groww" in config.products
    assert config.products["groww"].app_store_id
    assert config.products["groww"].play_package
    assert "google_docs" in config.mcp_servers
    assert "gmail" in config.mcp_servers


def test_all_five_products_present(project_root):
    config = load_config(project_root)
    expected = {"groww", "indmoney", "powerup", "wealth_monitor", "kuvera"}
    assert expected <= set(config.products.keys())
