"""Render 1920x1080 sections of a demo HTML page to PNGs with headless Chrome.

    uv run --no-project --with playwright python scripts/demo_render_html.py demo/part1/cards.html demo/part1/captures/cards
    uv run --no-project --with playwright python scripts/demo_render_html.py demo/part2/slides.html demo/part2/export --query all --selector .slide

Serves demo/ over a loopback HTTP server so pages can fetch captures/results.json.
"""
import argparse, functools, http.server, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'demo'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('page');p.add_argument('out')
    p.add_argument('--selector',default='.card')
    p.add_argument('--query',default='')
    args=p.parse_args()
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
    rel=(ROOT/args.page).resolve().relative_to(DEMO).as_posix()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
    handler=functools.partial(Quiet,directory=str(DEMO))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True)
            page=browser.new_page(viewport=dict(width=1920,height=1080),device_scale_factor=1)
            page.goto(f'http://127.0.0.1:{server.server_port}/{rel}'+(f'?{args.query}' if args.query else ''))
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(500)
            for i,el in enumerate(page.locator(args.selector).all(),1):
                name=(el.get_attribute('id') or f'{i:02d}')+'.png'
                el.screenshot(path=str(out/name),animations='disabled');print(out/name)
            browser.close()
    finally:server.shutdown()

if __name__=='__main__':main()
