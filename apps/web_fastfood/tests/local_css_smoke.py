"""Ensure dashboard styling is local, complete, and independent of a CDN."""

from pathlib import Path
import re
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


root = Path(__file__).resolve().parents[1]
pages = sorted((*root.joinpath("platform").rglob("*.html"), *root.joinpath("tenant").rglob("*.html")))
bundle = root / "shared" / "tailwind.css"
failures: list[str] = []

if not bundle.is_file() or bundle.stat().st_size < 10_000:
    failures.append("shared/tailwind.css is missing or unexpectedly small")
else:
    css = bundle.read_text(encoding="utf-8")
    # Include representative layout rules and arbitrary-value syntax used by
    # the platform login. These catch an empty or incorrectly-scanned build.
    for selector in (".hidden", ".flex", ".min-h-screen", ".w-16", ".max-w-\\[440px\\]"):
        if selector not in css:
            failures.append(f"compiled bundle is missing {selector}")

for page in pages:
    source = page.read_text(encoding="utf-8")
    relative = page.relative_to(root).as_posix()
    if "cdn.tailwindcss.com" in source:
        failures.append(f"{relative} still loads the Tailwind CDN")
    links = re.findall(r'<link[^>]+href="/shared/tailwind\.css\?v=1"[^>]*/?>', source)
    # kitchen.html is a deliberately self-contained KDS screen with its own
    # element CSS and no utility classes. Every utility-based page must load
    # the compiled bundle exactly once.
    expected_links = 1 if 'class="' in source else 0
    if len(links) != expected_links:
        failures.append(
            f"{relative} has {len(links)} local Tailwind links; expected {expected_links}"
        )


def serve_local(route):
    path = urlparse(route.request.url).path
    source = root / path.lstrip("/")
    if not source.is_file():
        route.fulfill(status=404)
        return
    content_types = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".png": "image/png",
        ".ico": "image/x-icon",
        ".webmanifest": "application/manifest+json",
    }
    route.fulfill(
        body=source.read_bytes(),
        content_type=content_types.get(source.suffix, "application/octet-stream"),
    )


if bundle.is_file():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        for area, expected_width, mark_selector, expected_mark_size in (
            ("platform", 440, "img[alt='STORIXX']", 64),
            # tenant login is a left/right split (brand panel + form panel),
            # not a single centered card — "width" here checks the brand
            # panel is exactly half the 1280px test viewport (md:w-1/2), and
            # the mark is the md:w-28/h-28 (112px) logo image, not the old
            # inline SVG mark this page used before the redesign.
            ("tenant", 640, "img[alt='STORIXX']", 112),
        ):
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.route("**/*", serve_local)
            page.goto(f"http://css.local/{area}/login.html", wait_until="load")
            card = page.locator("body > div").first.bounding_box()
            mark = page.locator(mark_selector).first.bounding_box()
            if page.locator("body").evaluate("element => getComputedStyle(element).display") != "flex":
                failures.append(f"{area} login body is not using the compiled flex layout")
            if not card or abs(card["width"] - expected_width) > 1:
                failures.append(f"{area} login width is not constrained to {expected_width}px")
            if not mark or abs(mark["width"] - expected_mark_size) > 1 or abs(mark["height"] - expected_mark_size) > 1:
                failures.append(f"{area} login mark is not {expected_mark_size}px square")
            page.close()
        browser.close()

print(f"{len(pages)} pages checked; {len(failures)} local CSS failure(s)")
for failure in failures:
    print(failure)
assert not failures
