"""Drive the running app in headless Chrome and capture 1920x1080 UI stills plus a walkthrough recording.

Requires the app at http://127.0.0.1:8765 and a local Google Chrome install:
    uv run --with playwright python scripts/demo_screenshots.py
Writes to demo/part1/captures/ui/.
"""
import argparse, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/part1/captures/ui'
SIZE=dict(width=1920,height=1080)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--name',default='Eye close-up')
    p.add_argument('--frame',type=int,default=50)
    p.add_argument('--mode',default='appearance')
    args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    video_dir=OUT/'_video'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True)
        ctx=browser.new_context(viewport=SIZE,device_scale_factor=1,record_video_dir=str(video_dir),record_video_size=SIZE)
        page=ctx.new_page()
        shot=lambda name,**kw:(page.screenshot(path=str(OUT/name),**kw),print(name))
        page.goto('http://127.0.0.1:8765')
        clip=page.locator('.clip',has_text=args.name)
        clip.wait_for()
        page.wait_for_timeout(1200)
        clip.click()
        frames=page.locator('.frame-controls span')
        for _ in range(400):
            current=int(frames.inner_text().split()[1])
            if current==args.frame:break
            page.get_by_label('Next outgoing frame' if current<args.frame else 'Previous outgoing frame').click()
        page.get_by_label('Ranking method').select_option(args.mode)
        refine=page.get_by_label('Refine incoming timing',exact=False)
        if refine.is_checked():refine.uncheck()
        page.mouse.move(0,0);page.wait_for_timeout(800)
        shot('01-library.png')

        page.locator('.workspace').scroll_into_view_if_needed()
        page.evaluate("window.scrollTo(0,document.querySelector('.workspace').getBoundingClientRect().top+scrollY-24)")
        page.wait_for_timeout(500)
        shot('02-outgoing-moment.png')
        page.locator('.source-panel').screenshot(path=str(OUT/'03-outgoing-panel.png'));print('03-outgoing-panel.png')
        page.locator('.search-options').evaluate("e=>e.style.outline='2px solid #c5ed80'")
        page.locator('.search-options').screenshot(path=str(OUT/'03b-mode-appearance-baseline.png'));print('03b-mode-appearance-baseline.png')
        page.locator('.search-options').evaluate("e=>e.style.outline=''")

        page.get_by_role('button',name='Find the next shot').click()
        page.wait_for_timeout(250)
        shot('04a-searching.png')
        page.locator('.match').first.wait_for(timeout=120_000)
        page.wait_for_timeout(1500)
        shot('04-results.png')
        page.locator('.results-panel').screenshot(path=str(OUT/'04b-results-panel.png'));print('04b-results-panel.png')

        page.get_by_role('button',name='Show inference evidence').click()
        page.wait_for_timeout(500)
        page.locator('.results-panel').screenshot(path=str(OUT/'05-inference-evidence.png'));print('05-inference-evidence.png')
        page.get_by_role('button',name='Hide inference evidence').click()

        page.locator('.match').first.click()
        page.locator('.editor video').wait_for(timeout=120_000)
        page.evaluate("window.scrollTo(0,document.querySelector('.editor').getBoundingClientRect().top+scrollY-24)")
        page.wait_for_timeout(2600)
        shot('06-editor-preview.png')

        page.get_by_role('button',name='Export 1080p MP4').click()
        page.get_by_text('Download transition').wait_for(timeout=180_000)
        page.wait_for_timeout(600)
        shot('07-export.png')
        page.locator('.adjust').screenshot(path=str(OUT/'07b-export-panel.png'));print('07b-export-panel.png')
        shot('08-full-page.png',full_page=True)
        page.wait_for_timeout(1000)
        recording=page.video.path()
        ctx.close();browser.close()
    shutil.move(recording,OUT/'walkthrough.webm');shutil.rmtree(video_dir,ignore_errors=True)
    print('walkthrough.webm')

if __name__=='__main__':main()
