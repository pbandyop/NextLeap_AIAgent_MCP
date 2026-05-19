import pytest

from pulse_agent.config.loader import load_config


@pytest.mark.parametrize(
    "product_id",
    ["groww", "indmoney", "powerup", "wealth_monitor", "kuvera"],
)
def test_all_products_config_valid(project_root, product_id):
    config = load_config(project_root)
    product = config.get_product(product_id)
    assert product.app_store_id
    assert product.play_package
    assert product.display_name
    assert product.window_weeks >= 1
