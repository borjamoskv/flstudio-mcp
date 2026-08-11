#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import os

STEM_IDS = [
    ('1ZbyMYutK6mk0YboCGG5M6JDCAl-e9xjF', '02_teddy_pendergrass_sample.wav'),
    ('1CQZNpxUCqEqstWizrbDXTB4JfISxD6DL', '03_bass.wav'),
    ('1_JkRWguLFcGj_fJ5C7yA3R-9-7b6ymFi', '04_claps.wav'),
    ('1hlEAA_3SEWcYbLrX8jks5m0G5Wrj-l9Y', '05_dub_synth_2.wav'),
    ('1UdHMPH_rgjla5SwQos3SwCQIsF4FNb0R', '06_dub_synth_1.wav'),
    ('1_Qkp88ALcVBXrArj7vq-1ndBMVHYvv9E', '07_low_end.wav'),
    ('1dJhFq2XB3fGBzkFaP_LSmPFRBBNUqst1', '08_shaker_2.wav'),
    ('1uItVVL23Zpy5MbfsI6mGklWER-Ji6YMe', '09_shakers.wav'),
    ('1lDPrVeeZjJgVKdGbtIWB1ASTL2vfupdG', '10_sinte_prin.wav'),
    ('1sFSXlMkCV0lp_HW_yjQOzEksKhq7FtOs', '11_top_loop.wav')
]

OUTPUT_DIR = os.path.expanduser('~/10_PROJECTS/No_Lo_Entiende_Stems')

def load_cookies(filepath):
    cookies = []
    with open(filepath, 'r') as f:
        for line in f:
            if not line or line.startswith('#'): continue
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                cookies.append({
                    'domain': parts[0],
                    'path': parts[2],
                    'secure': parts[3] == 'TRUE',
                    'name': parts[5],
                    'value': parts[6]
                })
    return cookies

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    cookies = load_cookies('/tmp/safari_google_cookies.txt')
    print(f"Loaded {len(cookies)} cookies from text file.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            headless=True
        )
        context = await browser.new_context(
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15'
        )
        await context.add_cookies(cookies)

        page = await context.new_page()
        page.set_default_timeout(10000)

        for fid, filename in STEM_IDS:
            output_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(output_path):
                print(f"Skipping {filename}, already exists.")
                continue
                
            url = f'https://drive.google.com/uc?id={fid}&export=download'
            print(f"Navigating to {url} for {filename}...")
            
            try:
                await page.goto(url)
                
                # Use page.locator to find the download button robustly
                # The button is usually a form submit or a link with id "uc-download-link"
                button = page.locator('form input[type="submit"], #uc-download-link').first
                
                if await button.count() > 0:
                    print(f"Found download button for {filename}, clicking...")
                    async with page.expect_download() as download_info:
                        await button.click()
                    download = await download_info.value
                    print(f"Downloading to {output_path}...")
                    await download.save_as(output_path)
                    print(f"Successfully saved {filename}")
                else:
                    # Maybe it downloaded directly or access was denied
                    print(f"Button not found for {filename}. Page title: {await page.title()}")
                    # Let's save a screenshot to see what's happening
                    await page.screenshot(path=f'/tmp/error_{filename}.png')
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                
            await asyncio.sleep(2)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
