#!/usr/bin/env python3
"""Check the TV display in headless Chromium at 1920x1080 for the given days.

Usage:  python3 scripts/check_display.py [YYYY-MM-DD ...] [--shots DIR]

With no dates, checks today and the next 6 days. For each day it loads index.html?previewDate=…
and fails if the page throws an error or the layout is bigger than the 1920x1080 canvas.
--shots saves a screenshot per day. Needs: pip install playwright && python -m playwright install chromium
"""
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from playwright.sync_api import sync_playwright

try:
    NZ = ZoneInfo('Pacific/Auckland')
except ZoneInfoNotFoundError:  # Windows without the tzdata package
    NZ = dt.timezone(dt.timedelta(hours=13))


def main():
    args = sys.argv[1:]
    shots = None
    if '--shots' in args:
        i = args.index('--shots')
        shots = args[i + 1]
        del args[i:i + 2]
        os.makedirs(shots, exist_ok=True)
    days = args or [(dt.datetime.now(NZ).date() + dt.timedelta(n)).isoformat() for n in range(7)]
    url = 'file://' + os.path.abspath('index.html').replace('\\', '/')
    if not url.startswith('file:///'):
        url = url.replace('file://', 'file:///')
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for day in days:
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            page.goto('%s?previewDate=%s' % (url, day))
            page.wait_for_timeout(1500)
            size = page.evaluate('() => [document.documentElement.scrollWidth, document.documentElement.scrollHeight]')
            if errors:
                problems.append('%s: page error: %s' % (day, errors[0][:200]))
            if size[0] > 1920 or size[1] > 1080:
                problems.append('%s: layout is %dx%d, bigger than 1920x1080' % (day, size[0], size[1]))
            if shots:
                page.screenshot(path=os.path.join(shots, day + '.png'))
            page.close()
        browser.close()
    if problems:
        print('\n'.join(problems))
        sys.exit(1)
    print('OK: %d day(s) fit 1920x1080 with no errors (%s).' % (len(days), ', '.join(days)))


if __name__ == '__main__':
    main()
