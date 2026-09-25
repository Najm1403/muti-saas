"""Exercise every tenant page's startup JavaScript against local API fixtures."""
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent / 'backend_fastfood'))
from app.main import app
pages = sorted((root / 'tenant').rglob('*.html'))
failures = []
requests = set()

def response_for(path):
    if path == '/api/v1/auth/me':
        return {'id': 'u1', 'tenant_id': 't1', 'full_name': 'Local tester',
                'username': 'tester', 'permissions': ['*'],
                'roles': ['Owner'], 'modules': ['dashboard', 'subscription',
                'settings', 'sales', 'reports', 'menu', 'promotions', 'deals',
                'branches', 'devices', 'kitchen', 'inventory', 'expenses',
                'employees', 'attendance', 'salaries', 'users', 'roles', 'activity']}
    if path == '/api/v1/dashboard':
        return {'branch_count': 1, 'active_branch_count': 1,
                'device_count': 1, 'active_device_count': 1, 'user_count': 2,
                'max_branches': 3, 'max_devices': 2, 'max_users': -1}
    if path == '/api/v1/devices/limits':
        return {'used': 0, 'limit': 10, 'max_devices': 10, 'current_devices': 0}
    if path in ('/api/v1/salaries/summary', '/api/v1/expenses/summary') or path.startswith('/api/v1/expenses/summary?'):
        return {}
    if path == '/api/v1/subscription':
        return {'max_branches': 3, 'max_devices': 2, 'max_users': -1}
    if path.startswith('/api/v1/salaries/register'):
        return {'rows': [], 'totals': {}}
    if path.startswith('/api/v1/activity'):
        return {'items': [], 'total': 0}
    if path.startswith('/api/v1/variants?'):
        return []
    if path.startswith('/api/v1/products/p1'):
        return {'id': 'p1', 'name': 'Test', 'category_id': 'c1', 'base_price': '1.00',
                'allow_inventory_tracking': False}
    return []

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    for source in pages:
        if source.name == 'login.html':
            continue
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.add_init_script("localStorage.setItem('tenant_token','local-test'); window.tailwind={}; window.lucide={createIcons(){}};")

        def route(r):
            path = r.request.url.split('tenant.local', 1)[-1].split('?', 1)[0]
            if path.startswith('/api/v1/'):
                requests.add((r.request.method, path))
                r.fulfill(json=response_for(path))
            elif path.startswith('/tenant/') or path.startswith('/shared/'):
                file = root / path.lstrip('/')
                if file.is_file():
                    r.fulfill(body=file.read_bytes(), content_type={'.html': 'text/html',
                        '.css': 'text/css', '.js': 'application/javascript'}.get(file.suffix, 'text/plain'))
                else:
                    r.fulfill(status=404)
            else:
                r.fulfill(body='', content_type='application/javascript')
        page.route('**/*', route)
        url = f'http://tenant.local/{source.relative_to(root).as_posix()}'
        if source.name == 'product-detail.html':
            url += '?product_id=p1&category_id=c1'
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_timeout(500)
        if source.name == 'subscription.html':
            expected = {'branchCount': '1/3', 'deviceCount': '1/2',
                        'userCount': '2/Unlimited'}
            for element_id, value in expected.items():
                if page.locator(f'#{element_id}').inner_text() != value:
                    failures.append(('subscription quotas', [
                        f'{element_id} did not render as {value}'
                    ]))
        if source.name == 'kitchen.html' and page.locator('#queue').inner_text() != 'No branches available.':
            failures.append((str(source.relative_to(root)), ['Empty kitchen branch state was not shown']))
        if errors:
            failures.append((str(source.relative_to(root)), errors))
        page.close()

    # Opening stock is entered directly in the Add Product drawer, gated
    # behind the tracking checkbox, and only for a brand-new product.
    page = browser.new_page()
    stock_errors = []
    page.on('pageerror', lambda error: stock_errors.append(str(error)))
    page.add_init_script("localStorage.setItem('tenant_token','local-test'); window.tailwind={}; window.lucide={createIcons(){}};")
    page.route('**/*', route)
    page.goto('http://tenant.local/tenant/menu.html', wait_until='domcontentloaded')
    page.evaluate('openProductDrawer(null)')
    page.locator('#drawerProdPrice').fill('100')
    # Tailwind's stylesheet is stubbed out in this harness, so a "hidden"
    # class toggle has no visual effect here (unlike responsive.js's native
    # .hidden property elsewhere in this file) — check the class directly.
    def opening_stock_hidden():
        return page.evaluate("document.getElementById('drawerOpeningStockField').classList.contains('hidden')")
    if not opening_stock_hidden():
        failures.append(('opening stock', ['Opening stock field was visible before tracking was enabled']))
    page.locator('#drawerAllowInventoryTracking').check()
    page.evaluate("toggleOpeningStockField(document.getElementById('drawerAllowInventoryTracking').checked)")
    if opening_stock_hidden():
        failures.append(('opening stock', ['Opening stock field stayed hidden after enabling tracking']))
    page.locator('#drawerOpeningStock').fill('25')
    if stock_errors:
        failures.append(('opening stock', stock_errors))
    page.close()

    # Business-template access is applied centrally by responsive.js. Exercise
    # both kinds of restriction: a hidden whole module (Kitchen/KDS) and a
    # disabled page-level capability (Add-on Groups inside the Menu module).
    restricted_me = response_for('/api/v1/auth/me') | {
        'modules': [m for m in response_for('/api/v1/auth/me')['modules'] if m != 'kitchen'],
        'business_features': {'variants': True, 'addons': False},
    }

    def restricted_route(r):
        path = r.request.url.split('tenant.local', 1)[-1].split('?', 1)[0]
        if path == '/api/v1/auth/me':
            r.fulfill(json=restricted_me)
        elif path.startswith('/api/v1/'):
            r.fulfill(json=response_for(path))
        elif path.startswith('/tenant/') or path.startswith('/shared/'):
            file = root / path.lstrip('/')
            if file.is_file():
                r.fulfill(body=file.read_bytes(), content_type={'.html': 'text/html',
                    '.css': 'text/css', '.js': 'application/javascript'}.get(file.suffix, 'text/plain'))
            else:
                r.fulfill(status=404)
        else:
            r.fulfill(body='', content_type='application/javascript')

    page = browser.new_page()
    page.add_init_script("localStorage.setItem('tenant_token','local-test'); window.tailwind={}; window.lucide={createIcons(){}};")
    page.route('**/*', restricted_route)
    page.goto('http://tenant.local/tenant/dashboard.html', wait_until='domcontentloaded')
    page.wait_for_timeout(500)
    if not page.locator('aside a[href="/tenant/addon-groups.html"]').first.is_hidden():
        failures.append(('template navigation', ['Disabled Add-on Groups link remained visible']))
    if not page.locator('aside a[href="/tenant/preparation-stations.html"]').first.is_hidden():
        failures.append(('template navigation', ['Hidden Kitchen/KDS link remained visible']))

    page.goto('http://tenant.local/tenant/addon-groups.html', wait_until='domcontentloaded')
    page.wait_for_timeout(500)
    if 'not part of your plan' not in page.locator('body').inner_text():
        failures.append(('template navigation', ['Disabled Add-on Groups page remained accessible']))

    page.goto('http://tenant.local/tenant/preparation-stations.html', wait_until='domcontentloaded')
    page.wait_for_timeout(500)
    if 'not part of your plan' not in page.locator('body').inner_text():
        failures.append(('template navigation', ['Hidden Kitchen/KDS page remained accessible']))

    page.goto('http://tenant.local/tenant/kitchen.html', wait_until='domcontentloaded')
    page.wait_for_timeout(500)
    if 'not part of your plan' not in page.locator('body').inner_text():
        failures.append(('template navigation', ['Hidden Kitchen Display page remained accessible']))
    page.close()
    browser.close()

for method, path in sorted(requests):
    if not any(route.path_regex.match(path) and method in (getattr(route, 'methods', None) or set())
               for route in app.routes if hasattr(route, 'path_regex')):
        failures.append(('route', [f'{method} {path} is not registered']))

print(f'{len(pages) - 1} tenant pages exercised; {len(failures)} startup or route failure(s)')
for file, errors in failures:
    print(file, errors)
assert not failures
