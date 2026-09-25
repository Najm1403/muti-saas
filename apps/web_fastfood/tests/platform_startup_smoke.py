"""Load platform pages locally and check startup API paths against FastAPI routes."""
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent / 'backend_fastfood'))
from app.main import app

pages = sorted((root / 'platform').glob('*.html'))
failures = []
requests = set()

def fixture(path):
    if path == '/api/platform/auth/me':
        return {'id': 'a1', 'full_name': 'Local admin', 'username': 'admin',
                'role': 'owner', 'is_super': True}
    if path.endswith('/salaries/register'):
        return {'period': '2026-09', 'rows': [], 'headcount': 0,
                'paid_count': 0, 'unpaid_count': 0, 'net_paid_total': '0',
                'net_pending_total': '0'}
    if path.endswith('/salaries/summary'):
        return {'by_month': [], 'by_department': []}
    if path.endswith('/reports/summary'):
        return {}
    if path.endswith('/settings'):
        return {}
    if path.endswith('/modules'):
        return []
    if path.endswith('/module-templates'):
        return []
    return []

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    for source in pages:
        if source.name == 'login.html':
            continue
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.add_init_script("localStorage.setItem('platform_token','local-test'); window.tailwind={}; window.lucide={createIcons(){}};")

        def route(r):
            path = r.request.url.split('platform.local', 1)[-1].split('?', 1)[0]
            if path.startswith('/api/platform/'):
                requests.add((r.request.method, path))
                r.fulfill(json=fixture(path))
            elif path.startswith(('/platform/', '/shared/')):
                file = root / path.lstrip('/')
                if file.is_file():
                    r.fulfill(body=file.read_bytes(), content_type={'.html': 'text/html',
                        '.css': 'text/css', '.js': 'application/javascript'}.get(file.suffix, 'text/plain'))
                else:
                    r.fulfill(status=404)
            else:
                r.fulfill(body='', content_type='application/javascript')

        page.route('**/*', route)
        url = f'http://platform.local/{source.relative_to(root).as_posix()}'
        if source.name == 'tenant-detail.html':
            url += '?id=11111111-1111-1111-1111-111111111111'
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_timeout(500)
        if errors:
            failures.append((source.name, errors))
        page.close()
    browser.close()

for method, path in sorted(requests):
    if not any(route.path_regex.match(path) and method in (getattr(route, 'methods', None) or set())
               for route in app.routes if hasattr(route, 'path_regex')):
        failures.append(('route', [f'{method} {path} is not registered']))

print(f'{len(pages) - 1} platform pages exercised; {len(failures)} startup or route failure(s)')
for source, errors in failures:
    print(source, errors)
assert not failures
