#!/usr/bin/env python3
"""Apply event changes approved by the admin team (from WhatsApp, via n8n) to index.html.

Usage:  python3 scripts/apply_update.py CHANGES.json [SUMMARY_OUT.json]

CHANGES.json:
  {"title": "Diwali & Annakut Utsav",
   "add":    [{"date": "8/11/2026", "event": "Deepotsav Aarti", "time": "8:00 PM", "source": "Mandir Programme"}],
   "remove": [{"date": "8/11/2026", "event": "Deepotsav Aarti"}]}

- "add" puts the event on the screen. If the same day already has an event with the same name (ignoring
  spelling variants, see sync_calendar.norm), that event is updated instead, so re-sending is safe.
  Fields left out keep their current value (e.g. a festival message written earlier).
- A picture for the event: "image": "images/NAME.jpg" (a file in images/, see scripts/prepare_image.py), optionally
  "imagePos" (which part shows, e.g. "center 30%") and "imageStyle" ("side" or "under"). "image": "none" takes it off.
- A video (an animation that plays silently on a loop, in the picture's place): "video": "videos/NAME.webm" (made with
  scripts/prepare_video.py, with the .mp4 beside it). "video": "none" takes it off; the picture, if any, stays.
- The day's colours from a poster: "palette": {"h": field hue, "s": saturation, "a": accent hue, "b": label hue}.
- "remove" takes the event off the list (same day, same name).
- Writes a CHANGELOG.md entry and a JSON summary: what was added, updated, removed or not found, and the dates.
"""
import datetime as dt
import json
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sync_calendar import norm

INDEX, CHANGELOG = 'index.html', 'CHANGELOG.md'
TEXT_FIELDS = ('event', 'time', 'note', 'source', 'quote', 'intro')
FLAGS = ('hideShlok', 'hidden')
IMAGE = re.compile(r'images/[\w.-]+\.(jpe?g|png|webp)')
VIDEO = re.compile(r'videos/[\w.-]+\.webm')
IMAGE_POS = re.compile(r'(left|center|right|top|bottom|\d{1,3}%)( (left|center|right|top|bottom|\d{1,3}%))?')


def today_nz():
    try:
        return dt.datetime.now(ZoneInfo('Pacific/Auckland')).date()
    except ZoneInfoNotFoundError:  # Windows without the tzdata package
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=13))).date()


def day_key(date):
    d, m, y = (int(p) for p in date.split('/'))
    return '%04d%02d%02d' % (y, m, d)


def clean_date(value):
    m = re.fullmatch(r'\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*', str(value or ''))
    if not m:
        raise ValueError('bad date %r (use D/M/YYYY)' % value)
    d, mo, y = (int(x) for x in m.groups())
    dt.date(y, mo, d)  # raises if the day doesn't exist
    return '%d/%d/%d' % (d, mo, y)


def clean_event(raw):
    e = {'date': clean_date(raw.get('date'))}
    for f in TEXT_FIELDS:
        v = re.sub(r'\s+', ' ', str(raw.get(f) or '')).strip()
        if v:
            e[f] = v
    if not e.get('event'):
        raise ValueError('an event on %s has no name' % e['date'])
    for f in FLAGS:
        if raw.get(f) is True:
            e[f] = True
    image = str(raw.get('image') or '').strip()
    if image == 'none':
        e['image'] = None  # taken off below
    elif image:
        if not IMAGE.fullmatch(image):
            raise ValueError('bad picture %r (use images/NAME.jpg)' % image)
        e['image'] = image
    video = str(raw.get('video') or '').strip()
    if video == 'none':
        e['video'] = None  # taken off below
    elif video:
        if not VIDEO.fullmatch(video):
            raise ValueError('bad video %r (use videos/NAME.webm)' % video)
        e['video'] = video
    pos = str(raw.get('imagePos') or '').strip()
    if pos and IMAGE_POS.fullmatch(pos):
        e['imagePos'] = pos
    if raw.get('imageStyle') in ('side', 'under'):
        e['imageStyle'] = raw['imageStyle']
    p = raw.get('palette')
    if isinstance(p, dict) and isinstance(p.get('h'), (int, float)):
        e['palette'] = {k: int(round(p[k])) for k in ('h', 's', 'a', 'b') if isinstance(p.get(k), (int, float))}
    return e


def label(e):
    d = dt.date(*reversed([int(p) for p in e['date'].split('/')]))
    return '%s %s' % ('%d %s' % (d.day, d.strftime('%b')), e['event'])


def main():
    changes = json.load(open(sys.argv[1], encoding='utf-8'))
    today = today_nz().isoformat()
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    html = open(INDEX, encoding='utf-8').read()
    m = re.search(r'const EVENTS = (\[.*?\]);\n', html, re.S)
    events = json.loads(m.group(1))
    same = lambda a, b: day_key(a['date']) == day_key(b['date']) and norm(a['event']) == norm(b['event'])

    summary = {'added': [], 'updated': [], 'removed': [], 'not_found': [], 'dates': []}
    for raw in changes.get('remove') or []:
        target = {'date': clean_date(raw.get('date')), 'event': str(raw.get('event') or '').strip()}
        # hidden entries stay: they stop the weekly calendar sync adding the event back
        hits = [e for e in events if same(e, target) and not e.get('hidden')]
        if not hits:
            summary['not_found'].append(label(target))
            continue
        events = [e for e in events if e not in hits]
        summary['removed'].append(label(target))
        summary['dates'].append(target['date'])

    for raw in changes.get('add') or []:
        new = clean_event(raw)
        old = next((e for e in events if same(e, new) and not e.get('hidden')), None)
        if old:
            before = dict(old)
            old.update(new)
            if old.get('image', '') is None:
                for f in ('image', 'imagePos', 'imageStyle'):
                    old.pop(f, None)
            if old.get('video', '') is None:
                old.pop('video')
            if old != before:
                summary['updated'].append(label(new))
        else:
            for f in ('image', 'video'):
                if new.get(f, '') is None:
                    new.pop(f)
            new.setdefault('progress', False)
            events.append(new)
            summary['added'].append(label(new))
        summary['dates'].append(new['date'])

    summary['dates'] = sorted(set(summary['dates']), key=day_key)
    if not (summary['added'] or summary['updated'] or summary['removed']):
        print('Nothing to change.')
    else:
        # Same order as the calendar sync: by date, festivals before programme items (the page sorts too).
        events.sort(key=lambda e: (day_key(e['date']), 1 if e.get('source') else 0))
        body = '[\n' + ',\n'.join('  ' + json.dumps(e, ensure_ascii=False) for e in events) + '\n]'
        html = html[:m.start(1)] + body + html[m.end(1):]
        assert len(json.loads(re.search(r'const EVENTS = (\[.*?\]);\n', html, re.S).group(1))) == len(events)

        title = str(changes.get('title') or '').strip()
        lines = []
        for what, key in (('Added', 'added'), ('Updated', 'updated'), ('Removed', 'removed')):
            if summary[key]:
                lines.append('  - %s: %s' % (what, '; '.join(summary[key])))
        entry = '## %s\n- **From the admin team (WhatsApp)%s:**\n%s\n\n' % (
            today, ' — ' + title if title else '', '\n'.join(lines))
        log = open(CHANGELOG, encoding='utf-8').read()
        i = log.index('\n## ') + 1
        open(INDEX, 'w', encoding='utf-8').write(html)
        open(CHANGELOG, 'w', encoding='utf-8').write(log[:i] + entry + log[i:])
        print('Added %d, updated %d, removed %d.' % (len(summary['added']), len(summary['updated']), len(summary['removed'])))
    if summary['not_found']:
        print('Not found: ' + '; '.join(summary['not_found']))
    if out_path:
        json.dump(summary, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
