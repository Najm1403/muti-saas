"""Guard the tenant Sales page against exposing internal UUIDs as business data."""

from pathlib import Path


page = (Path(__file__).resolve().parents[1] / "tenant" / "sales.html").read_text(
    encoding="utf-8"
)

assert "s.user_id?.slice" not in page, "Sales UI still renders the cashier UUID."
assert "s.cashier_name || s.cashier_username" in page
assert "escapeHTML(s.sale_number" in page
assert ">Cashier</th>" in page

print("sales UI smoke: human sale number and cashier identity are rendered")
