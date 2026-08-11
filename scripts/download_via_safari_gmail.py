#!/usr/bin/env python3
import time
import subprocess
import pyautogui

def run_applescript(script):
    p = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.decode('utf-8').strip(), err.decode('utf-8').strip()

def main():
    print("1. Scrolling down in Safari to render all attachments...")
    script_scroll = '''
    tell application "Safari"
        activate
        tell window 1
            do JavaScript "window.scrollTo(0, document.body.scrollHeight);" in current tab
        end tell
    end tell
    '''
    run_applescript(script_scroll)
    time.sleep(2)
    
    print("2. Clicking ALL download elements in email body...")
    script_js = '''
    tell application "Safari"
        tell window 1
            do JavaScript "
                let els = Array.from(document.querySelectorAll('div[role=\\"button\\"], a, span')).filter(el => {
                    let label = el.getAttribute('aria-label') || el.getAttribute('data-tooltip') || el.getAttribute('title') || '';
                    return label.toLowerCase().includes('descargar') || label.toLowerCase().includes('download');
                });
                
                let count = 0;
                els.forEach((el, idx) => {
                    setTimeout(() => {
                        el.click();
                    }, idx * 1000);
                    count++;
                });
                
                'Found and clicked ' + count + ' download elements!';
            " in current tab
        end tell
    end tell
    '''
    out, err = run_applescript(script_js)
    print(f"JS Result: {out}")
    if err:
        print(f"JS Error: {err}")

if __name__ == '__main__':
    main()
