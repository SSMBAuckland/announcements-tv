#!/usr/bin/env python3
"""Remove pictures and videos of events that are long past, so the site stays small and quick for the TVs.

Usage:  python3 scripts/cleanup_media.py [--days 30] [--dry-run]

- A file in images/ or videos/ is removed once every event that uses it (as "image", "video" or
  "backgroundVideo") is more than --days days in the past (Auckland time). The MP4 made beside a WebM
  goes with it.
- Those events keep their text; only the picture/video setting is taken off them, so previewing an
  old day still works.
- Files no event uses at all are left alone (they may be waiting to be added), but are listed.
- Writes a CHANGELOG.md entry for what it removed. Does nothing if nothing is due.
The files stay in the git history, so anything removed can be brought back if needed.
"""
import argparse
import datetime as dt
import json
import os
import re
from zoneinfo import ZoneInfo

INDEX, CHANGELOG = 'index.html', 'CHANGELOG.md'
FIELDS = ('image', 'video', 'backgroundVideo')
DIRS = ('images', 'videos')


def event_date(e):
    d, m, y = (int(p) for p in e['date'].split('/'))
    return dt.date(y, m, d)


def companions(path):
    """The file and the MP4 made beside a WebM (prepare_video.py writes both)."""
    out = [path]
    if path.endswith('.webm'):
        out.append(path[:-5] + '.mp4')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=30)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    today = dt.datetime.now(ZoneInfo('Pacific/Auckland')).date()
    cutoff = today - dt.timedelta(days=a.days)
    html = open(INDEX, encoding='utf-8').read()
    m = re.search(r'const EVENTS = (\[.*?\]);\n', html, re.S)
    events = json.loads(m.group(1))

    # newest date each file is used on
    last_use = {}
    for e in events:
        for f in FIELDS:
            if e.get(f):
                for p in companions(e[f]):
                    last_use[p] = max(last_use.get(p, dt.date.min), event_date(e))
    due = {p for p, d in last_use.items() if d < cutoff}
    files = sorted(os.path.join(d, n) for d in DIRS if os.path.isdir(d) for n in os.listdir(d))
    remove = [p for p in files if p in due]
    unused = [p for p in files if p not in last_use]
    if unused:
        print('Not used by any event (left alone):', ', '.join(unused))
    if not remove:
        print('Nothing to remove (no pictures or videos older than %d days).' % a.days)
        return
    freed = sum(os.path.getsize(p) for p in remove)
    print('Removing %d file(s), %.1f MB: %s' % (len(remove), freed / 1e6, ', '.join(remove)))
    if a.dry_run:
        return

    for p in remove:
        os.remove(p)
    # take the setting off the past events, and only off those (a later event may share the name)
    for e in events:
        for f in FIELDS:
            if e.get(f) in due and event_date(e) < cutoff:
                del e[f]
    body = '[\n' + ',\n'.join('  ' + json.dumps(e, ensure_ascii=False) for e in events) + '\n]'
    html = html[:m.start(1)] + body + html[m.end(1):]
    open(INDEX, 'w', encoding='utf-8').write(html)

    entry = '## %s\n- **Media clean-up:** removed %d picture/video file%s of events more than %d days past (%.1f MB): %s. The events stay; only their picture or video setting was taken off. The files are still in the git history.\n\n' % (
        today.isoformat(), len(remove), '' if len(remove) == 1 else 's', a.days, freed / 1e6, ', '.join('`%s`' % p for p in remove))
    log = open(CHANGELOG, encoding='utf-8').read()
    i = log.index('\n## ') + 1
    open(CHANGELOG, 'w', encoding='utf-8').write(log[:i] + entry + log[i:])


if __name__ == '__main__':
    main()
