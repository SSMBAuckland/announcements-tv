#!/usr/bin/env python3
"""Helper for .github/workflows/whatsapp-update.yml (changes the admin team asks for on WhatsApp, via n8n).

  python3 scripts/whatsapp_job.py prompt     Claude Code's instructions for the request in $REQUEST
  python3 scripts/whatsapp_job.py dates      days to check: the days the change touched, plus the coming week
  python3 scripts/whatsapp_job.py result     works out what happened and writes it to /tmp/result.json
  python3 scripts/whatsapp_job.py callback   sends /tmp/result.json to n8n (N8N_CALLBACK_URL, N8N_CALLBACK_KEY)
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    NZ = ZoneInfo('Pacific/Auckland')
except ZoneInfoNotFoundError:  # Windows without the tzdata package
    NZ = dt.timezone(dt.timedelta(hours=13))
PAGE = 'https://ssmbauckland.github.io/announcements-tv/'
RESULT = '/tmp/result.json'

PROMPT = """A member of the SSMB Auckland admin team asked for this change to the mandir's TV display, by WhatsApp:

<request>
{request}
</request>

Make the change in this repository. The display is index.html. Read CLAUDE.md and README.md first and follow them, \
especially the minimum text sizes (the screen is read from across the hall).
- For plain event additions, changes and removals you can use: python3 scripts/apply_update.py CHANGES.json \
(the format is at the top of that file). It also writes the CHANGELOG.md entry.
- Otherwise add a CHANGELOG.md entry yourself.
- Check every day you changed: python3 scripts/check_display.py YYYY-MM-DD ... (it must report no errors and a \
1920x1080 fit). Fix anything it reports.
- Do not commit or push. This workflow does that after its own check.
- If the request is unclear, or can't be done without breaking the rules in CLAUDE.md, change nothing and reply \
with a question starting with "QUESTION:".

Your final reply is posted in the admin team's WhatsApp group: at most three short sentences of plain text (no \
markdown, no headings), saying what you changed and on which dates. Never mention n8n there; if you need to refer to \
the bot's settings, call them "the WAHA config"."""

LIMIT = re.compile(r'usage limit|hit your .{0,40}limit|limit reached|limit will reset|resets? (at )?\d|'
                   r'credit balance is too low|out of (extra )?usage|rate.?limit', re.I)


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True).stdout


def changed_dates():
    """Days whose EVENTS lines changed (added or removed lines in index.html)."""
    out = set()
    for line in git('diff', '-U0', '--', 'index.html').splitlines():
        if line[:1] in '+-' and not line.startswith(('+++', '---')):
            for d, m, y in re.findall(r'"date": "(\d{1,2})/(\d{1,2})/(\d{4})"', line):
                out.add(dt.date(int(y), int(m), int(d)))
    return out


def reset_time(text, now):
    """When a Claude limit resets, from messages like 'resets 3:45pm', 'resets Oct 24, 3pm' or 'limit reached|1760000000'."""
    m = re.search(r'limit reached\|(\d{9,})', text)
    if m:
        when = dt.datetime.fromtimestamp(int(m.group(1)), NZ)
        return when if when > now else None
    m = re.search(r'resets?\s+(?:at\s+)?(?:([A-Z][a-z]{2,8})\s+(\d{1,2}),?\s+(?:at\s+)?)?(\d{1,2})(?::(\d{2}))?\s*([ap]m)', text, re.I)
    if not m:
        return None
    mon, day, hour, minute, ampm = m.groups()
    hour = int(hour) % 12 + (12 if ampm.lower() == 'pm' else 0)
    when = now.replace(hour=hour, minute=int(minute or 0), second=0, microsecond=0)
    if mon:
        try:
            month = dt.datetime.strptime(mon[:3], '%b').month
            when = when.replace(month=month, day=int(day))
            if when < now - dt.timedelta(days=1):
                when = when.replace(year=when.year + 1)
        except ValueError:
            pass
    elif when <= now:
        when += dt.timedelta(days=1)
    return when


def result():
    now = dt.datetime.now(NZ)
    kind = os.environ.get('KIND', 'events')
    out = {'ref': os.environ.get('REF', ''), 'kind': kind, 'billing': os.environ.get('BILLING', ''),
           'model': os.environ.get('MODEL', ''), 'status': 'failed', 'summary': '', 'changes': {}, 'dates': [],
           'cost_usd': 0, 'reset_at': 0, 'reset_text': '',
           'run_url': '%s/%s/actions/runs/%s' % (os.environ.get('GITHUB_SERVER_URL', ''),
                                                 os.environ.get('GITHUB_REPOSITORY', ''), os.environ.get('GITHUB_RUN_ID', ''))}
    changed = bool(git('status', '--porcelain', '--', 'index.html').strip())
    days = sorted(changed_dates())
    out['dates'] = [d.isoformat() for d in days]
    if days:
        out['preview_url'] = '%s?previewDate=%s' % (PAGE, days[0].isoformat())

    if kind == 'events':
        try:
            out['changes'] = json.load(open('/tmp/summary.json', encoding='utf-8'))
        except (OSError, ValueError):
            err = open('/tmp/apply.err', encoding='utf-8', errors='replace').read().strip() if os.path.exists('/tmp/apply.err') else ''
            out['summary'] = 'The event changes could not be applied: ' + (err.splitlines()[-1] if err else 'no details.')
            return finish(out)
        out['status'] = 'done' if changed else 'nochange'
    else:
        raw = ''
        try:
            raw = open('/tmp/claude.json', encoding='utf-8').read()
            c = json.loads(raw)
        except (OSError, ValueError):
            c = {}
        err = open('/tmp/claude.err', encoding='utf-8', errors='replace').read() if os.path.exists('/tmp/claude.err') else ''
        text = str(c.get('result') or '').strip()
        out['cost_usd'] = round(float(c.get('total_cost_usd') or 0), 4)
        failed = c.get('is_error') or c.get('subtype') not in (None, 'success') or not c
        if text == 'NO_PRO_TOKEN':
            out.update(status='limit', reason='no_pro', reset_at=int((now + dt.timedelta(hours=7)).timestamp()), reset_text='')
        elif failed and LIMIT.search(text + '\n' + err + '\n' + raw[:2000]):
            when = reset_time(text + '\n' + err, now) or now + dt.timedelta(hours=7)
            out['status'] = 'limit'
            out['reason'] = 'credit' if re.search(r'credit balance', text + err, re.I) else 'limit'
            out['reset_at'] = int(when.timestamp())
            out['reset_text'] = when.strftime('%I:%M %p').lstrip('0').replace(':00 ', ' ') + \
                ('' if when.date() == now.date() else when.strftime(' %a %d %b').replace(' 0', ' '))
            out['summary'] = text[:300]
        elif c.get('subtype') == 'error_max_budget_usd':
            out['summary'] = 'Stopped at the spending cap for one change; nothing was published.'
        elif failed:
            last_err = err.strip().splitlines()[-1] if err.strip() else ''
            out['summary'] = (text or last_err or 'Claude Code stopped with an error.')[:300]
        elif text.upper().startswith('QUESTION:'):
            out['status'] = 'question'
            out['summary'] = text.split(':', 1)[1].strip()[:700]
        else:
            out['status'] = 'done' if changed else 'nochange'
            out['summary'] = text[:700]
    if out['status'] == 'done' and os.environ.get('CHECK') == 'failure':
        out['status'] = 'failed'
        out['summary'] = 'The change did not pass the display check, so nothing was published. ' + \
                         open('/tmp/check.txt', encoding='utf-8', errors='replace').read().strip()[:300]
    return finish(out)


def finish(out):
    json.dump(out, open(RESULT, 'w', encoding='utf-8'), ensure_ascii=False)
    gh = os.environ.get('GITHUB_OUTPUT')
    if gh:
        with open(gh, 'a', encoding='utf-8') as f:
            f.write('status=%s\n' % out['status'])
    print(json.dumps(out, ensure_ascii=False, indent=1))


def callback():
    url, key = os.environ.get('N8N_CALLBACK_URL'), os.environ.get('N8N_CALLBACK_KEY')
    if not url:
        print('N8N_CALLBACK_URL is not set; not reporting back.')
        return
    out = json.load(open(RESULT, encoding='utf-8')) if os.path.exists(RESULT) else {
        'ref': os.environ.get('REF', ''), 'kind': os.environ.get('KIND', ''), 'status': 'failed',
        'summary': 'The update job stopped before it finished.'}
    if out.get('status') == 'done' and os.environ.get('SCREENS') not in ('success', None, ''):
        out['screens'] = os.environ.get('SCREENS')
    if os.environ.get('COMMIT'):
        out['commit'] = os.environ['COMMIT']
    req = urllib.request.Request(url, data=json.dumps(out, ensure_ascii=False).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json', 'X-SSMB-Key': key or '',
                                          'User-Agent': 'ssmb-tv-workflow'})
    with urllib.request.urlopen(req, timeout=30) as r:
        print('Reported to n8n:', r.status)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'prompt':
        print(PROMPT.format(request=os.environ.get('REQUEST', '').strip()))
    elif cmd == 'dates':
        today = dt.datetime.now(NZ).date()
        days = changed_dates() | {today + dt.timedelta(n) for n in range(7)}
        print(' '.join(d.isoformat() for d in sorted(days)))
    elif cmd == 'result':
        result()
    elif cmd == 'callback':
        callback()
    else:
        sys.exit(__doc__)
