#!/usr/bin/env python3
"""Daily health check of the live TV display. Run by .github/workflows/daily-health-check.yml.

Usage:  python3 scripts/health_check.py [--url URL]

Checks, and exits 1 with a list of problems if any fail:
- the live website answers, and shows the latest version of index.html (so a stuck website update is caught);
- today and the next two days load on the live site without page errors, fit 1920x1080, and their pictures
  and videos load and play (scripts/check_display.py --url);
- the last refresh of the Yodeck screens did not fail.
Also warns (without failing) when the event list is running out, or nothing at all is listed for two weeks.
Writes the report to health-report.md for the workflow to use.
"""
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from zoneinfo import ZoneInfo

LIVE = 'https://ssmbauckland.github.io/announcements-tv/'
NZ = ZoneInfo('Pacific/Auckland')


def fetch(url):
    req = urllib.request.Request(url + ('&' if '?' in url else '?') + 'health=%d' % dt.datetime.now().timestamp(),
                                 headers={'User-Agent': 'ssmb-tv-health-check', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


def main():
    url = sys.argv[sys.argv.index('--url') + 1] if '--url' in sys.argv else LIVE
    today = dt.datetime.now(NZ).date()
    problems, warnings = [], []

    # 1. the website answers, with the current version
    local = open('index.html', 'rb').read()
    try:
        status, live = fetch(url)
        if status != 200:
            problems.append('The website answered with status %d.' % status)
        elif hashlib.sha256(live).digest() != hashlib.sha256(local).digest():
            # allow for a website update that is still on its way
            age = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', 'index.html'], capture_output=True, text=True).stdout.strip()
            mins = (dt.datetime.now().timestamp() - int(age)) / 60 if age else 999
            if mins > 30:
                problems.append('The website is showing an older version of the display than the latest change '
                                '(made %d minutes ago). The GitHub Pages update may be stuck: check the Actions tab.' % mins)
    except Exception as e:  # noqa: BLE001 - any failure to load is the problem we report
        problems.append('The website could not be loaded: %s' % e)

    # 2. the next three days display correctly on the live site
    days = [(today + dt.timedelta(n)).isoformat() for n in range(3)]
    r = subprocess.run([sys.executable, 'scripts/check_display.py', *days, '--url', url], capture_output=True, text=True)
    if r.returncode != 0:
        problems.extend(line for line in (r.stdout + r.stderr).strip().splitlines() if line.strip())

    # 3. the last screen refresh worked (needs the gh CLI and a token; skipped without them)
    repo = os.environ.get('GITHUB_REPOSITORY')
    if repo and os.environ.get('GH_TOKEN'):
        out = subprocess.run(['gh', 'api', 'repos/%s/actions/workflows/refresh-yodeck.yml/runs?per_page=1' % repo],
                             capture_output=True, text=True)
        try:
            run = json.loads(out.stdout)['workflow_runs'][0]
            if run.get('conclusion') == 'failure':
                problems.append('The last refresh of the TV screens (Yodeck) failed: %s' % run.get('html_url'))
        except (ValueError, KeyError, IndexError):
            pass

    # 4. warnings about the event list
    m = re.search(r'const EVENTS = (\[.*?\]);\n', local.decode('utf-8'), re.S)
    events = [e for e in json.loads(m.group(1)) if not e.get('hidden')]
    dates = sorted(dt.date(*reversed([int(p) for p in e['date'].split('/')])) for e in events)
    upcoming = [d for d in dates if d >= today]
    if not upcoming or upcoming[-1] < today + dt.timedelta(days=45):
        warnings.append('The event list ends on %s. Add the next events (the weekly calendar sync adds them '
                        'if they are in the Bhuj Mandir calendar).' % (upcoming[-1].strftime('%-d %b %Y') if upcoming else 'a past date'))
    if not [d for d in upcoming if d <= today + dt.timedelta(days=14)]:
        warnings.append('Nothing is listed for the next two weeks.')

    lines = ['# TV display health check: %s' % today.strftime('%A %-d %B %Y'), '']
    if problems:
        lines += ['**Problems found:**', ''] + ['- ' + p for p in problems] + ['']
    else:
        lines += ['All good: the website is up to date and today plus the next two days display correctly.', '']
    if warnings:
        lines += ['**Heads up:**', ''] + ['- ' + w for w in warnings] + ['']
    report = '\n'.join(lines)
    open('health-report.md', 'w', encoding='utf-8').write(report)
    print(report)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('problems=%d\nwarnings=%d\n' % (len(problems), len(warnings)))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
