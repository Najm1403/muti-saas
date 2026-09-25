"""Exercise the tenant expense list and summary with a populated local fixture."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
summary = {'date_from': '2026-09-01', 'date_to': '2026-09-30', 'count': 1,
           'by_month': [{'month': '2026-09', 'total': '10.00'}],
           'by_category': [{'category_id': 'c1', 'name': 'Food & Supplies',
                            'total': '10.00', 'budget': '50.00', 'count': 1}]}
expense = {'id': 'x1', 'expense_date': '2026-09-12', 'category_id': 'c1',
           'category_name': 'Food & Supplies', 'amount': '10.00',
           'payment_method': 'Cash', 'vendor': 'Local vendor'}

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.add_init_script("localStorage.setItem('tenant_token','test'); window.tailwind={}; window.lucide={createIcons(){}};")

    def route(r):
        path = r.request.url.split('expense.local', 1)[-1].split('?', 1)[0]
        if path.startswith('/api/v1/'):
            if path == '/api/v1/auth/me':
                body = {'full_name': 'Tester', 'permissions': ['*'],
                        'modules': ['expenses'], 'roles': ['Owner']}
            elif path == '/api/v1/expenses/summary':
                body = summary
            elif path == '/api/v1/expenses/categories':
                body = [{'id': 'c1', 'name': 'Food & Supplies'}]
            elif path == '/api/v1/expenses':
                body = [expense]
            else:
                body = []
            r.fulfill(json=body)
        elif path.startswith(('/tenant/', '/shared/')):
            file = root / path.lstrip('/')
            if file.is_file():
                r.fulfill(body=file.read_bytes(), content_type={'.html': 'text/html',
                    '.css': 'text/css', '.js': 'application/javascript'}.get(file.suffix, 'text/plain'))
            else:
                r.fulfill(status=404)
        else:
            r.fulfill(body='', content_type='application/javascript')

    page.route('**/*', route)
    page.goto('http://expense.local/tenant/expenses.html')
    expect(page.locator('#rows tr')).to_have_count(1)
    expect(page.locator('#kpiTop')).to_have_text('Food & Supplies')
    expect(page.locator('#rows')).to_contain_text('Local vendor')
    assert not errors, errors
    browser.close()
print('PASS: populated tenant expense summary and list')
