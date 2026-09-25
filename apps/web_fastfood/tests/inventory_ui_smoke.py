"""Run with Python + Playwright; all HTTP requests use local fixtures."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import os
import sys

root = Path(__file__).resolve().parents[1]
variants = [
    dict(id='v1', product_id='p1', product_name='Laptop', option_value_ids=[], tracks_inventory=True, stock_by_branch={'b1': 5, 'b2': 2}, variant_name='Default variant'),
    dict(id='v2', product_id='p2', product_name='Burger', option_value_ids=[], tracks_inventory=False, stock_by_branch=None, variant_name='Default variant'),
    dict(id='v3', product_id='p3', product_name='Phone', option_value_ids=['red'], tracks_inventory=True, stock_by_branch={'b1': 0, 'b2': 8}, variant_name='Colors: Red'),
]
errors = []
requests = []
failures = {}

def route(r):
    path = r.request.url.split('inventory.test')[-1].split('?')[0]
    method = r.request.method
    requests.append((method, path))
    if failures.get(path, 0):
        failures[path] -= 1
        r.fulfill(status=503, json={'detail': 'Temporary service failure'})
        return
    if path == '/api/v1/auth/me': body = {'full_name': 'Admin', 'permissions': ['*'], 'roles': ['Owner']}
    elif path == '/api/v1/branches/': body = [
        {'id': 'b1', 'name': 'Main', 'branch_code': 'MAIN'},
        {'id': 'b2', 'name': 'Outlet', 'branch_code': 'OUT'},
    ]
    elif path == '/api/v1/variants': body = variants
    elif path.endswith('/stock/increase'):
        variants[0]['stock_by_branch']['b1'] += r.request.post_data_json['quantity']; body = variants[0]
    elif path.endswith('/stock/decrease'):
        variants[0]['stock_by_branch']['b1'] -= r.request.post_data_json['quantity']; body = variants[0]
    elif path.endswith('/stock'):
        variants[0]['stock_by_branch']['b1'] = r.request.post_data_json['stock_quantity']; body = variants[0]
    elif path.endswith('/history'):
        body = [{'created_at': '2026-09-11T10:00:00Z', 'adjustment_type': 'manual_set', 'quantity_change': 5, 'resulting_quantity': 5, 'note': 'Count'}]
    elif path.startswith('/tenant/') or path.startswith('/shared/'):
        file = root / path.lstrip('/')
        if file.exists():
            content = file.read_text(encoding='utf-8')
            if file.suffix == '.html': content = content.replace('</head>', '<style>.hidden{display:none}</style></head>')
            r.fulfill(body=content, content_type={'.html': 'text/html', '.css': 'text/css'}.get(file.suffix, 'application/javascript'))
            return
        r.fulfill(status=404); return
    else:
        r.fulfill(body=''); return
    r.fulfill(json=body)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel=os.environ.get('INVENTORY_BROWSER_CHANNEL', 'msedge' if sys.platform == 'win32' else 'chromium'))
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/*', route)
    page.add_init_script("localStorage.setItem('tenant_token','test-token')")
    page.goto('http://inventory.test/tenant/inventory.html')
    expect(page.locator('#skuRows tr')).to_have_count(2)
    expect(page.locator('#skuRows')).not_to_contain_text('Burger')
    expect(page.locator('#skuRows')).to_contain_text('Laptop')
    # Scoped to the SKU table specifically — the page now also has Stock
    # Report, Stock Movement, and Stock Transfers tables (each its own tab,
    # hidden via CSS but still present in the DOM), so an unscoped
    # 'table thead th' matches all four tables' headers combined, not just
    # this one.
    expect(page.locator('table:has(#skuRows) thead th')).to_have_count(4)
    expect(page.locator('#refreshInventory')).to_have_count(1)
    page.locator('#inventorySearch').fill('phone')
    expect(page.locator('#skuRows tr')).to_have_count(1)
    expect(page.locator('#skuRows')).to_contain_text('Phone / Colors: Red')
    page.locator('#inventoryStockFilter').select_option('out_of_stock')
    expect(page.locator('#skuRows tr')).to_have_count(1)
    page.locator('#branchSelect').select_option('b2')
    expect(page.locator('#skuRows tr')).to_have_count(0)
    page.locator('#inventoryStockFilter').select_option('in_stock')
    expect(page.locator('#skuRows tr')).to_have_count(1)
    page.locator('#inventorySearch').fill('')
    expect(page.locator('#skuRows tr')).to_have_count(2)
    page.locator('#inventoryStockFilter').select_option('all')
    page.locator('#branchSelect').select_option('b1')
    laptop_row = page.locator('#skuRows tr').filter(has_text='Laptop')
    laptop_row.get_by_role('button', name='Increase', exact=True).click()
    page.locator('#stockQuantity').fill('2')
    page.locator('#saveSkuStock').click()
    expect(page.locator('#skuRows')).to_contain_text('7')
    laptop_row.get_by_role('button', name='Decrease', exact=True).click()
    page.locator('#stockQuantity').fill('1')
    page.locator('#saveSkuStock').click()
    laptop_row.get_by_role('button', name='Set stock', exact=True).click()
    page.locator('#stockQuantity').fill('12')
    failures['/api/v1/variants/v1/stock'] = 1
    page.locator('#saveSkuStock').click()
    expect(page.locator('#stockError')).to_contain_text('Temporary service failure')
    expect(page.locator('#stockDialog')).to_be_visible()
    page.locator('#saveSkuStock').click()
    expect(page.locator('#skuRows')).to_contain_text('12')
    laptop_row.get_by_role('button', name='History', exact=True).click()
    expect(page.locator('#skuHistory')).to_contain_text('manual_set')
    page.get_by_role('button', name='Close', exact=True).click()
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.locator('.sku-action').count() == 10
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.locator('#refreshInventory').click()
    expect(page.locator('#skuRows tr')).to_have_count(2)
    expect(page.locator('#inventoryError')).to_be_empty()
    assert ('GET', '/api/v1/variants') in requests
    assert not any('/inventory/variants' in path or '/serials' in path for _, path in requests)
    assert not errors, errors
    browser.close()
print('PASS: active variant endpoints, quantity stock actions, recovery, history, responsive layout, and no JS errors')

