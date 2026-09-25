"""Menu variant-detail regression for create-time colors and stock summaries."""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect, sync_playwright


root = Path(__file__).resolve().parents[1]
product = {
    "id": "p1", "category_id": "c1", "name": "Phone", "product_code": "PHONE",
    "description": None, "sku": None, "warranty": None, "is_active": True,
    "price": 500, "default_variant_id": "v0", "allow_inventory_tracking": True,
    "has_combination_variants": True,
}
branches = [
    {"id": "b1", "name": "Main", "branch_code": "MAIN", "is_active": True},
    {"id": "b2", "name": "Outlet", "branch_code": "OUT", "is_active": True},
]
groups = [{"id": "g-color", "name": "Colors"}, {"id": "g-ram", "name": "RAM"}]
options = {
    "g-color": [
        {"id": "red", "option_group_id": "g-color", "name": "Red"},
        {"id": "blue", "option_group_id": "g-color", "name": "Blue"},
    ],
    "g-ram": [{"id": "8gb", "option_group_id": "g-ram", "name": "8 GB"}],
}
links = [
    {"id": "link-color", "option_group_id": "g-color", "usage_type": "specification",
     "is_required": True, "allowed_option_ids": [], "min_selections": 1,
     "max_selections": 1, "default_option_id": None},
    {"id": "link-ram", "option_group_id": "g-ram", "usage_type": "inventory_component",
     "is_required": False, "allowed_option_ids": [], "min_selections": 0,
     "max_selections": 1, "default_option_id": None},
]
variants = [
    {"id": "v0", "product_id": "p1", "option_value_ids": [],
     "variant_name": "Default variant", "sale_price": 500, "tracks_inventory": True,
     "is_default": True, "stock_by_branch": {"b1": 0, "b2": 0}},
    {"id": "v-red", "product_id": "p1", "option_value_ids": ["red"],
     "variant_name": "Colors: Red", "sale_price": 500, "tracks_inventory": True,
     "is_default": False, "stock_by_branch": {"b1": 5, "b2": 2}},
    {"id": "v-blue", "product_id": "p1", "option_value_ids": ["blue"],
     "variant_name": "Colors: Blue", "sale_price": 525, "tracks_inventory": True,
     "is_default": False, "stock_by_branch": {"b1": 3, "b2": 4}},
]
requests = []
errors = []
created_products = []


def route(request_route):
    parsed = urlparse(request_route.request.url)
    path = parsed.path
    if path.startswith("/api/v1/"):
        requests.append((request_route.request.method, path, parsed.query))
        if request_route.request.method == "POST" and path == "/api/v1/products/":
            payload = request_route.request.post_data_json
            created_products.append(payload)
            request_route.fulfill(json={**product, **payload, "id": "created-product"})
            return
        if request_route.request.method != "GET":
            request_route.fulfill(status=405, json={"detail": "Unexpected write"})
            return
        if path == "/api/v1/auth/me":
            body = {"full_name": "Menu tester", "username": "tester", "roles": [],
                    "tenant": {"name": "Test Shop", "code": "TEST"}}
        elif path == "/api/v1/business/template-config":
            body = {"product_fields": {"sku": True, "specs": False, "warranty": True},
                    "variants": {"enabled": True}, "addons": {"enabled": False},
                    "inventory": {"tracking_forced_on": False}}
        elif path == "/api/v1/business/":
            body = {"name": "Test Shop"}
        elif path == "/api/v1/categories/":
            body = [{"id": "c1", "name": "Phones", "description": None,
                     "display_order": 1, "is_active": True}]
        elif path == "/api/v1/products/":
            body = []
        elif path == "/api/v1/products/p1":
            body = product
        elif path == "/api/v1/branches/":
            body = branches
        elif path == "/api/v1/products/p1/branches":
            body = {"all_branches": True, "branches": branches}
        elif path == "/api/v1/variant-option-groups/":
            body = groups
        elif path == "/api/v1/products/p1/variant-option-groups":
            body = links
        elif path == "/api/v1/variant-options/":
            body = options[parse_qs(parsed.query)["option_group_id"][0]]
        elif path == "/api/v1/variants":
            body = variants
        else:
            body = []
        request_route.fulfill(json=body)
        return

    source = root / path.lstrip("/")
    if source.is_file():
        request_route.fulfill(
            body=source.read_bytes(),
            content_type={".html": "text/html", ".css": "text/css", ".js": "application/javascript",
                          ".png": "image/png"}.get(source.suffix, "application/octet-stream"),
        )
    else:
        request_route.fulfill(status=404)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.route("**/*", route)
    page.add_init_script("localStorage.setItem('tenant_token', 'test')")
    url = "http://menu.test/tenant/menu/product-detail.html?product_id=p1&category_id=c1"
    page.goto(url, wait_until="load")

    expect(page.get_by_text("Priced Variants", exact=True)).to_have_count(0)
    expect(page.get_by_label("This product is trackable")).to_have_count(0)
    expect(page.locator("#productTrackableStatus")).to_have_text("Trackable")
    expect(page.locator("#prodPriceField")).to_be_hidden()
    expect(page.get_by_role("heading", name="Overall Stock")).to_be_visible()
    expect(page.locator("[data-overall-stock]")).to_have_text("14")
    expect(page.locator("[data-color-stock-row]")).to_have_count(2)

    red = page.locator("[data-color-stock-row]").filter(has_text="Red")
    blue = page.locator("[data-color-stock-row]").filter(has_text="Blue")
    expect(red).to_contain_text("Total: 7")
    expect(red).to_contain_text("Main")
    expect(red).to_contain_text("Outlet")
    expect(blue).to_contain_text("Total: 7")
    expect(page.locator("#variantGroupsGrid")).to_contain_text("RAM")
    expect(page.locator("#variantGroupsGrid")).not_to_contain_text("Colors")

    # A plain product shows the one SKU's overall and per-branch stock as a
    # read-only summary; later adjustments belong to Inventory.
    product["has_combination_variants"] = False
    variants[:] = [{
        "id": "v0", "product_id": "p1", "option_value_ids": [],
        "variant_name": "Default variant", "sale_price": 500, "tracks_inventory": True,
        "is_default": True, "stock_by_branch": {"b1": 4, "b2": 6},
    }]
    page.reload(wait_until="load")
    expect(page.locator("#prodPriceField")).to_be_visible()
    expect(page.locator("[data-overall-stock]")).to_have_text("10")
    expect(page.locator("[data-color-stock-row]")).to_have_count(0)
    expect(page.locator("#stockSectionBody input")).to_have_count(0)
    expect(page.locator("#stockSectionBody")).to_contain_text("Main (MAIN)")
    expect(page.locator("#stockSectionBody")).to_contain_text("Use Inventory to adjust stock")
    assert not any(path.endswith("/stock") for method, path, _ in requests if method != "GET")

    assert any(path == "/api/v1/variants" and query == "product_id=p1"
               for _, path, query in requests)

    # The Add Product form remains the one place colors are chosen. Verify
    # that each checked color sends its sale price and opening stock for all
    # assigned branches in the atomic product-create request.
    create_page = browser.new_page()
    create_page.on("pageerror", lambda error: errors.append(str(error)))
    create_page.route("**/*", route)
    create_page.add_init_script("localStorage.setItem('tenant_token', 'test')")
    create_page.goto("http://menu.test/tenant/menu.html", wait_until="load")
    create_page.get_by_role("button", name="Add Product").click()
    create_page.locator("#drawerProdName").fill("Color Phone")
    create_page.locator("#drawerProdCode").fill("COLOR_PHONE")
    create_page.locator("#drawerProdPrice").fill("500")
    create_page.locator("#drawerAllowInventoryTracking").check()
    create_page.locator("#drawerHasColors").check()
    red_row = create_page.locator('[data-color-id="red"]')
    expect(red_row).to_be_visible()
    red_row.locator(".color-check").check()
    red_row.locator(".color-price").fill("550")
    red_row.locator(".color-stock").fill("7")
    create_page.get_by_role("button", name="Save Product").click()
    expect(create_page.get_by_text("Product created")).to_be_visible()
    assert len(created_products) == 1
    payload = created_products[0]
    assert payload["priced_variant_group_id"] == "g-color"
    assert payload["priced_variants"] == [{
        "option_id": "red", "sale_price": 550,
        "opening_stock_by_branch": {"b1": 7, "b2": 7},
    }]
    assert "opening_stock_by_branch" not in payload
    create_page.close()

    assert not errors, errors
    browser.close()

print("PASS: create-time color pricing/stock payload and overall/per-color stock summaries are correct")
