"""Local dashboard script and stored-text regression checks; no live API writes."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from html.parser import HTMLParser
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/"web_fastfood"
class Scripts(HTMLParser):
    def __init__(self): super().__init__();self.active=False;self.scripts=[];self.part=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script": self.active=not dict(attrs).get("src");self.part=[]
    def handle_data(self,data):
        if self.active:self.part.append(data)
    def handle_endtag(self,tag):
        if tag=="script" and self.active:self.scripts.append("".join(self.part));self.active=False
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
results={"script_errors":[],"pages_checked":0}
with sync_playwright() as browser_tool:
    browser=browser_tool.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page()
    for source in ROOT.rglob("*.html"):
        parser=Scripts();parser.feed(source.read_text(encoding="utf-8"))
        results["pages_checked"]+=1
        for index,script in enumerate(parser.scripts):
            error=page.evaluate("source => {try {new Function(source); return null;} catch(e) {return e.message;}}",script)
            if error: results["script_errors"].append({"file":str(source.relative_to(ROOT)),"script":index,"error":error})
    payload="<img src=x onerror=window.__injected=1> O'Reilly"
    def respond(route):
        path=route.request.url
        if "/promotions/" in path:
            data=[{"id":"11111111-1111-1111-1111-111111111111","name":payload,"promo_code":payload,
                "type":"PERCENTAGE","discount_value":"10","used_count":0,"max_uses":None,"is_active":True,"all_branches":True}]
        elif "/auth/me" in path:
            data={"id":"11111111-1111-1111-1111-111111111111","full_name":"Test","tenant_id":"11111111-1111-1111-1111-111111111111","permissions":["*"],"enabled_modules":None}
        else:data=[]
        route.fulfill(status=200,content_type="application/json",body=json.dumps(data))
    page.add_init_script("localStorage.setItem('tenant_token','browser-test'); window.tailwind={}; window.lucide={createIcons(){}};")
    page.route("**/api/**",respond)
    page.route("https://**",lambda route:route.fulfill(status=200,content_type="application/javascript",body=""))
    page.goto(f"http://127.0.0.1:{server.server_port}/tenant/promotions.html",wait_until="domcontentloaded")
    page.wait_for_function("typeof renderTable === 'function'")
    page.evaluate("value => { promotions=[{id:'11111111-1111-1111-1111-111111111111',name:value,promo_code:value,type:'PERCENTAGE',discount_value:10,used_count:0,is_active:true}];renderTable(); }",payload)
    results["injection_executed"]=page.evaluate("Boolean(window.__injected)")
    results["injected_elements"]=page.locator("#tableBody img").count()
    results["literal_text_visible"]=payload in page.locator("#tableBody").inner_text()
    # Inline event argument encoder must preserve quotes without creating executable code.
    results["event_argument_roundtrip"]=page.evaluate("""() => {
      window.received=null;window.capture=value=>window.received=value;
      const value="O'Reilly');window.__injected=1;//";
      const holder=document.createElement('div');holder.innerHTML=`<button onclick="capture('${escapeJSAttribute(value)}')">Test</button>`;
      holder.firstChild.click();return window.received===value&&!window.__injected;
    }""")
    browser.close()
server.shutdown()
print(json.dumps(results,indent=2))
assert not results["script_errors"] and not results["injection_executed"] and results["injected_elements"]==0 and results["literal_text_visible"] and results["event_argument_roundtrip"]
