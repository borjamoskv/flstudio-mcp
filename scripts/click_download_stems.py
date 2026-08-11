#!/usr/bin/env python3
import pyautogui
import time
from PIL import Image
import os
import subprocess

STEM_IDS = [
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

OUTPUT_DIR = os.path.expanduser('~/Downloads')

def find_blue_button_and_click():
    screenshot_path = '/tmp/screen.png'
    os.system(f'screencapture -x {screenshot_path}')
    img = Image.open(screenshot_path).convert('RGB')
    width, height = img.size
    
    # Google Drive blue button color: rgb(26, 115, 232)
    target_r, target_g, target_b = 26, 115, 232
    tolerance = 20
    
    # Search from center outwards or just scan
    # The button is usually centrally aligned vertically below the text
    found_x, found_y = -1, -1
    for y in range(int(height*0.2), int(height*0.8), 5):
        for x in range(int(width*0.2), int(width*0.8), 5):
            r, g, b = img.getpixel((x, y))
            if abs(r - target_r) < tolerance and abs(g - target_g) < tolerance and abs(b - target_b) < tolerance:
                found_x, found_y = x, y
                break
        if found_x != -1:
            break
            
    if found_x != -1:
        # Click the center of the button
        # MacOS retina display means coordinates are halved for pyautogui
        click_x = found_x // 2
        click_y = found_y // 2
        print(f"Found blue button at {click_x}, {click_y}")
        pyautogui.click(click_x, click_y)
        return True
    return False

def main():
    for fid, filename in STEM_IDS:
        url = f'https://drive.google.com/uc?id={fid}&export=download'
        print(f"Opening {filename}...")
        subprocess.run(['open', '-a', 'Google Chrome', url])
        time.sleep(3.5) # Wait for page load
        
        # Try to find and click the blue button
        success = find_blue_button_and_click()
        if not success:
            print("Blue button not found by color, using Tab+Enter fallback...")
            # Fallback: Tab 3 times and Enter
            for _ in range(4):
                pyautogui.press('tab')
                time.sleep(0.2)
            pyautogui.press('enter')
            
        time.sleep(1) # wait for download to start
        pyautogui.hotkey('command', 'w') # Close tab
        time.sleep(0.5)

if __name__ == '__main__':
    main()
