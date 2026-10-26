#!/usr/bin/env python3
"""Helper for .github/workflows/whatsapp-update.yml (changes the admin team asks for on WhatsApp, via n8n).

  python3 scripts/whatsapp_job.py prompt     Claude Code's instructions for the request in $REQUEST
  python3 scripts/whatsapp_job.py images     brings the pictures in $IMAGES from the incoming branch into images/
  python3 scripts/whatsapp_job.py dates      days to check: the days the change touched, plus the coming week
  python3 scripts/whatsapp_job.py result     works out what happened and writes it to /tmp/result.json
  python3 scripts/whatsapp_job.py callback   sends /tmp/result.json to n8n (N8N_CALLBACK_URL, N8N_CALLBACK_KEY)
"""
import base64
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
- Pictures: an event can show a picture in the Today card with "image": "images/NAME.jpg" (README, "Pictures"). \
Pictures named in the request are already in images/, cropped to the subject; look at each one first (Read it). \
Choose "imagePos" so faces and murtis stay in view, never put text over a face, and keep every text size.
- Colours from a poster: give the event a "palette" (README) so the day's colours match the poster the admins \
shared. The field always stays dark and the text light.
- A festive ("fancy") look is about the occasion itself, not only lights: Diwali has diyas and rangoli, Raksha \
Bandhan a rakhi thread, Janmashtami a flute, peacock feather and makhan matki, Navratri garba and dandiya, Holi \
coloured powder, Sharad Poonam the full moon, Hindola a decorated swing, Annakut the Govardhan offering, a visit by \
Acharya Maharaj or Lalji Maharaj a welcome toran and flowers, national days the flag colours. Build it like the \
existing ones (a SPECIAL_PALETTES entry with its own FESTIVAL_ART, named on the day's events with "theme"), keep it \
faint behind the text, and match any picture or poster the admins sent.
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
AUTH = re.compile(r'oauth token (has )?(expired|been revoked)|invalid (bearer|oauth|api) ?(token|key)|authentication.?(error|failed)|'
                  r'not logged in|please run /login|invalid x-api-key|\b401\b', re.I)


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


def images():
    """Fetch the pictures in $IMAGES from the incoming branch, then crop and shrink them into images/."""
    try:
        items = json.loads(os.environ.get('IMAGES') or '[]')
    except ValueError:
        items = []
    failed = []
    for it in items if isinstance(items, list) else []:
        src, dst, crop = (str(it.get(k) or '') for k in ('from', 'to', 'crop'))
        if not re.fullmatch(r'incoming/[\w.-]+', src) or not re.fullmatch(r'images/[\w.-]+\.jpg', dst):
            failed.append(dst or src or '?')
            continue
        data = subprocess.run(['git', 'show', 'origin/incoming:' + src], capture_output=True).stdout
        if not data:
            failed.append(dst)
            continue
        with open('/tmp/picture-in', 'wb') as f:
            f.write(data)
        args = [sys.executable, 'scripts/prepare_image.py', '/tmp/picture-in', dst]
        if re.fullmatch(r'\d+(\.\d+)?(,\d+(\.\d+)?){3}', crop):
            args += ['--crop', crop]
        r = subprocess.run(args, capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip()[-300:])
        if r.returncode:
            failed.append(dst)
    if failed:
        open('/tmp/images.err', 'w', encoding='utf-8').write(', '.join(failed))
        print('Pictures not brought in: ' + ', '.join(failed))


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
    asked = [d for d in os.environ.get('DATES', '').replace(' ', '').split(',') if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d)]
    if days or asked:
        out['preview_url'] = '%s?previewDate=%s' % (PAGE, days[0].isoformat() if days else asked[0])

    if kind == 'login':
        try:
            out.update(json.load(open('/tmp/login.json', encoding='utf-8')))
        except (OSError, ValueError):
            out['summary'] = 'The login job stopped before it finished.'
        return finish(out)
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
        elif failed and out['billing'] == 'pro' and AUTH.search(text + '\n' + err + '\n' + raw[:2000]):
            # the Pro plan login has expired or was signed out: the bot asks the admins to log in again
            out.update(status='limit', reason='auth', reset_at=int((now + dt.timedelta(hours=7)).timestamp()), reset_text='')
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
    if os.path.exists('/tmp/images.err'):
        out['summary'] = (out['summary'] + ' ' if out['summary'] else '') + \
            'Some pictures could not be brought in (' + open('/tmp/images.err', encoding='utf-8').read().strip() + ').'
    if out['status'] == 'done' and os.environ.get('CHECK') == 'failure':
        out['status'] = 'failed'
        out['summary'] = 'The change did not pass the display check, so nothing was published. ' + \
                         open('/tmp/check.txt', encoding='utf-8', errors='replace').read().strip()[:300]
    if out['status'] == 'done' and os.environ.get('PREVIEW'):
        save_preview(out)
    return finish(out)


def put_incoming(path, data):
    """Upload a file to the incoming branch (the body goes on stdin: a picture is too big for an argument)."""
    body = json.dumps({'message': 'Preview ' + path, 'content': base64.b64encode(data).decode(), 'branch': 'incoming'})
    return subprocess.run(['gh', 'api', '-X', 'PUT', 'repos/%s/contents/%s' % (os.environ.get('GITHUB_REPOSITORY', ''), path), '--input', '-'],
                          input=body, capture_output=True, text=True).returncode == 0


def save_preview(out):
    """After a fancy design: screenshots of its days go to preview/<id>/ on the incoming branch. The change is
    published as usual; the bot then shows the screenshots in the group and asks whether it is right or needs changes.
    A screenshot that can't be saved doesn't stop the change; the bot then asks without it."""
    pid = os.environ.get('PREVIEW', '')
    if not re.fullmatch(r'[\w.-]+', pid):
        return
    asked = [d for d in os.environ.get('DATES', '').replace(' ', '').split(',') if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d)]
    days = (asked or [d.isoformat() for d in sorted(changed_dates())] or [dt.datetime.now(NZ).date().isoformat()])[:3]
    shots_dir = '/tmp/preview-shots'
    subprocess.run([sys.executable, 'scripts/check_display.py', *days, '--shots', shots_dir], capture_output=True, text=True)
    raw = 'https://raw.githubusercontent.com/%s/incoming/' % os.environ.get('GITHUB_REPOSITORY', '')
    shots = []
    for d in days:
        png = os.path.join(shots_dir, d + '.png')
        if not os.path.exists(png):
            continue
        path, data = 'preview/%s/%s.png' % (pid, d), open(png, 'rb').read()
        try:  # a JPEG is a fraction of the size, quicker to open on a phone
            from PIL import Image
            Image.open(png).convert('RGB').save(png[:-4] + '.jpg', 'JPEG', quality=82, optimize=True)
            path, data = path[:-4] + '.jpg', open(png[:-4] + '.jpg', 'rb').read()
        except Exception:
            pass
        if put_incoming(path, data):
            shots.append(raw + path)
    out['preview'] = {'id': pid, 'dates': days, 'shots': shots, 'live': True}


def finish(out):
    json.dump(out, open(RESULT, 'w', encoding='utf-8'), ensure_ascii=False)
    gh = os.environ.get('GITHUB_OUTPUT')
    if gh:
        with open(gh, 'a', encoding='utf-8') as f:
            f.write('status=%s\n' % out['status'])
    print(json.dumps(out, ensure_ascii=False, indent=1))
    # one line the bot looks for when it reads this run's log
    print('SSMB_RESULT ' + json.dumps(out, ensure_ascii=False))


def callback():
    url, key = os.environ.get('N8N_CALLBACK_URL'), os.environ.get('N8N_CALLBACK_KEY')
    out = json.load(open(RESULT, encoding='utf-8')) if os.path.exists(RESULT) else {
        'ref': os.environ.get('REF', ''), 'kind': os.environ.get('KIND', ''), 'status': 'failed',
        'summary': 'The update job stopped before it finished.'}
    if out.get('status') == 'done' and os.environ.get('SCREENS') not in ('success', None, ''):
        out['screens'] = os.environ.get('SCREENS')
    if os.environ.get('COMMIT'):
        out['commit'] = os.environ['COMMIT']
    if not url:
        print('No direct report address set; the bot reads the result from this run instead.')
        return
    data = json.dumps(out, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST',
                                 headers={'Content-Type': 'application/json', 'X-SSMB-Key': key or '',
                                          'User-Agent': 'ssmb-tv-workflow'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print('Reported back:', r.status)
            return
    except urllib.error.HTTPError as e:
        print('Report refused:', e.code, e.headers.get('server'), e.headers.get('cf-ray'), e.read()[:300])
    # second try with curl (a different client fingerprint)
    r = subprocess.run(['curl', '-sS', '-o', '/dev/stderr', '-w', '%{http_code}', '-X', 'POST', url, '-H', 'Content-Type: application/json',
                        '-H', 'X-SSMB-Key: ' + (key or ''), '-A', 'ssmb-tv-workflow', '--data-binary', '@-'],
                       input=data, capture_output=True)
    # Not fatal: the bot also checks finished runs every minute and reads the SSMB_RESULT line.
    print('curl:', r.stdout.decode(), r.stderr.decode()[:200])


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'prompt':
        print(PROMPT.format(request=os.environ.get('REQUEST', '').strip()))
    elif cmd == 'dates':
        today = dt.datetime.now(NZ).date()
        days = changed_dates() | {today + dt.timedelta(n) for n in range(7)}
        for d in os.environ.get('DATES', '').replace(' ', '').split(','):  # the days a preview shows
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d):
                days.add(dt.date.fromisoformat(d))
        print(' '.join(d.isoformat() for d in sorted(days)))
    elif cmd == 'images':
        images()
    elif cmd == 'result':
        result()
    elif cmd == 'callback':
        callback()
    else:
        sys.exit(__doc__)
