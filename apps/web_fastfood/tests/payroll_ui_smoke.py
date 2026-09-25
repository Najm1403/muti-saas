"""Exercise tenant and platform payroll search/payment UI with local fixtures."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
employee = {'employee_id': 'e1', 'employee_no': 'E001', 'full_name': 'A&B Worker',
            'monthly_salary': '100.00', 'status': 'unpaid', 'payment_id': None}
register = {'period': '2026-09', 'rows': [employee], 'headcount': 1,
            'paid_count': 0, 'unpaid_count': 1, 'net_paid_total': '0',
            'net_pending_total': '0'}

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    for area in ('tenant', 'platform'):
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.add_init_script("localStorage.setItem('tenant_token','test'); localStorage.setItem('platform_token','test'); window.tailwind={}; window.lucide={createIcons(){}};")

        def route(r):
            path = r.request.url.split('payroll.local', 1)[-1].split('?', 1)[0]
            if path.startswith('/api/'):
                if path.endswith('/register'):
                    body = register
                elif path.endswith('/summary'):
                    body = {'by_month': []}
                elif path.endswith('/auth/me'):
                    body = {'is_super': True, 'role': 'owner', 'permissions': ['*'],
                            'modules': ['salaries'], 'full_name': 'Tester'}
                else:
                    body = []
                r.fulfill(json=body)
            elif path.startswith(('/tenant/', '/platform/', '/shared/')):
                file = root / path.lstrip('/')
                if file.is_file():
                    r.fulfill(body=file.read_bytes(), content_type={'.html': 'text/html',
                        '.css': 'text/css', '.js': 'application/javascript'}.get(file.suffix, 'text/plain'))
                else:
                    r.fulfill(status=404)
            else:
                r.fulfill(body='', content_type='application/javascript')

        page.route('**/*', route)
        page.goto(f'http://payroll.local/{area}/salaries.html')
        expect(page.locator('#rows tr')).to_have_count(1)
        page.locator('#fQ').fill('A&B')
        expect(page.locator('#rows tr')).to_have_count(1)
        page.get_by_role('button', name='Record', exact=True).click()
        expect(page.locator('#payModal')).to_be_visible()
        expect(page.locator('#payWho')).to_contain_text('A&B Worker')
        assert not errors, (area, errors)
        page.close()
    browser.close()
print('PASS: tenant and platform salary search and payment dialog')
