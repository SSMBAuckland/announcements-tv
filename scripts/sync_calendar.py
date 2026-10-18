#!/usr/bin/env python3
"""Weekly sync: add new events from the Bhuj Mandir Google Calendar to index.html.

Usage:  python3 scripts/sync_calendar.py [ICS_URL_OR_FILE]

Rules
- Additive only: events already on the screen are never changed or removed, so anything
  edited by hand (times, notes, themes, Mandal programmes) is safe.
- Only dates from today (Auckland) onwards are considered.
- An event counts as "already there" when the same day has an event with the same name,
  ignoring spelling variants such as Poojan/Pujan, "Fast", "Vrat".
- The same curation as the 2027 import: daily/monthly observances, pujari instructions,
  astronomical notes and individual Shraddh days are left out (see DROP below).
- New festivals reuse the festival message already written for the same festival.
- Writes a CHANGELOG.md entry listing what was added. Exits 0 with no changes if nothing is new.
"""
import datetime as dt
import json
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

ICS_URL = ('https://calendar.google.com/calendar/ical/'
           '5d4109444691faf38bcb2f2846bab586b617dc98275c18ac2611276449fd74e8%40group.calendar.google.com/public/basic.ics')
INDEX, CHANGELOG = 'index.html', 'CHANGELOG.md'

# Not shown on the TV: daily/monthly observances, ritual instructions for the pujaris,
# astronomical notes, Snan/Kamurta notices and the individual daily Shraddh days.
DROP = re.compile(r'^(Pradosh Vrat|Masik Shivratri|Amas|Vrat ni Poonam|Sun enters|Holashtak|Kamurta|'
                  r'(Vaishakh|Maagh) Snan|Mahalay of|Saubhagyavati|Sam Shravani|Shraddh of (children|those)|'
                  r'(Ekam|Bij|Trij|Choth|Pancham|Chhath|Satam|Aatham|Nom|Dasham|Ekadashi|Baras|Teras|Chaudas|Poonam-Amas) Shraddh)', re.I)
DROP_WHOLE = re.compile(r'^(Today|From today|Offer|Swing|Sam Shravani|Sun enters)\b', re.I)
HISTORY = re.compile(r'^(Birth of|Shree Hari (gave|celebrated|installed|performed|left)|Shreeji Maharaj|Shree Hari\'s Swadham|'
                     r'Shree Nilkanth Varni (took|arrived)|Today Shree Nilkanth|Pattabhishek|Day of the manifestation|Sadguru Ramanand Swami gave)')
# Calendar spelling -> spelling of an existing event that already has a festival message.
QUOTE_ALIAS = {'annakutotsav': 'annkutotsav', 'dhan teras': 'dhanteras', 'kali chaudas': 'kali chaudash',
               'laxmi poojan': 'laxmi pujan', 'chopada poojan': 'chopda pujan', 'govardhan poojan': 'govardhan pujan',
               'hanuman poojan': 'hanuman pujan', 'saraswati poojan': 'saraswati pujan',
               'tulsi vivah begins': 'tulsi wedding begins', 'tulsi vivah ends': 'tulsi wedding ends',
               'dattatreya jayanti': 'datatrey jayanti', 'new year begins': 'nutan varsharambh'}


def norm(name):
    """Name key that ignores spelling variants, for duplicate detection."""
    n = name.lower()
    for a, b in (('poojan', 'pujan'), ('chopada', 'chopda'), ('annakut', 'annkut'), ('vivah', 'wedding'),
                 ('shraddh', 'shradh'), ('dattatreya', 'datatrey'), ('dhan teras', 'dhanteras'),
                 ('chaudas', 'chaudash'), ('panchmi', 'panchami')):
        n = n.replace(a, b)
    n = re.sub(r'\b(fast|vrat)\b', '', n)
    return re.sub(r'[^a-z0-9]', '', n)


def read_ics(src):
    if re.match(r'https?://', src):
        with urllib.request.urlopen(src, timeout=60) as r:
            raw = r.read().decode('utf-8')
    else:
        raw = open(src, encoding='utf-8').read()
    raw = re.sub(r'\r?\n[ \t]', '', raw.replace('\r\n', '\n'))
    unesc = lambda s: s.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
    out = []
    for blk in raw.split('BEGIN:VEVENT')[1:]:
        d = {}
        for line in blk.split('END:VEVENT')[0].strip().split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                d.setdefault(k.split(';')[0], v)
        if d.get('DTSTART') and re.match(r'^\d{8}', d['DTSTART']):
            out.append({'start': d['DTSTART'][:8], 'summary': unesc(d.get('SUMMARY', ''))})
    return out


def curate(cal, quotes, from_key):
    clean = lambda s: re.sub(r'\s+', ' ', s).strip().rstrip('.')
    rows = []
    for x in sorted((c for c in cal if c['start'] >= from_key), key=lambda c: c['start']):
        d = x['start']
        date = '%d/%d/%s' % (int(d[6:8]), int(d[4:6]), d[:4])
        en = x['summary'].split(' / ')[0].strip()          # English part of "English / ગુજરાતી"
        if not en or DROP_WHOLE.search(en):
            continue
        main, _, instr = en.partition('; ')
        items = []
        for part in [p.strip() for p in main.split(', ')]:
            if not items:
                items.append([part, []])
            elif re.match(r'^Samvat \d+', part) or part[:1].islower() or len(part.split()) > 6:
                items[-1][1].append(part[:1].upper() + part[1:])      # history / instruction -> note
            elif items[-1][1] and re.search(r'Samvat \d+$', items[-1][1][-1]):
                items[-1][1].append(part)                             # place after "Samvat 18xx"
            else:
                items.append([part, []])
        if instr and items:
            items[-1][1].append(instr[:1].upper() + instr[1:])
        for name, notes in items:
            name = clean(name)
            if DROP.search(name):
                continue
            progress = False
            if name.endswith(' Fast'):
                progress = 'Ekadashi' in name
                name = name[:-5]
            r = {'date': date, 'event': name}
            if notes:
                r['note'] = ' • '.join(clean(n) for n in notes)
            r['progress'] = progress
            q = quotes.get(name.lower()) or quotes.get(QUOTE_ALIAS.get(name.lower(), ''))
            if q:
                r['quote'] = q
            if HISTORY.search(name):
                r['history'] = True
            rows.append(r)
    return rows


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ICS_URL
    html = open(INDEX, encoding='utf-8').read()
    m = re.search(r'const EVENTS = (\[.*?\]);\n', html, re.S)
    existing = json.loads(m.group(1))
    key = lambda d: '%04d%02d%02d' % tuple(reversed([int(p) for p in d.split('/')]))
    have = {(key(e['date']), norm(e['event'])) for e in existing}
    quotes = {}
    for e in existing:
        if e.get('quote'):
            quotes.setdefault(e['event'].lower(), e['quote'])

    today = dt.datetime.now(ZoneInfo('Pacific/Auckland')).strftime('%Y%m%d')
    new = [r for r in curate(read_ics(src), quotes, today) if (key(r['date']), norm(r['event'])) not in have]
    seen, added = set(), []
    for r in new:
        k = (key(r['date']), norm(r['event']))
        if k not in seen:
            seen.add(k)
            added.append(r)
    if not added:
        print('No new calendar events.')
        return

    # Insert after the last existing event that isn't a Mandal programme, sorted by date (the page sorts too).
    merged = existing + added
    merged.sort(key=lambda e: (key(e['date']), 1 if e.get('source') else 0))
    body = '[\n' + ',\n'.join('  ' + json.dumps(e, ensure_ascii=False) for e in merged) + '\n]'
    html = html[:m.start(1)] + body + html[m.end(1):]
    assert len(json.loads(re.search(r'const EVENTS = (\[.*?\]);\n', html, re.S).group(1))) == len(merged)
    open(INDEX, 'w', encoding='utf-8').write(html)

    fmt = lambda r: '%s %s' % (dt.date(*reversed([int(p) for p in r['date'].split('/')])).strftime('%-d %b %Y'), r['event'])
    lines = '\n'.join('  - ' + fmt(r) for r in added[:40]) + ('\n  - … and %d more' % (len(added) - 40) if len(added) > 40 else '')
    entry = '## %s\n- **Calendar sync:** added %d new event%s from the Bhuj Mandir calendar:\n%s\n\n' % (
        dt.datetime.now(ZoneInfo('Pacific/Auckland')).strftime('%Y-%m-%d'), len(added), '' if len(added) == 1 else 's', lines)
    log = open(CHANGELOG, encoding='utf-8').read()
    i = log.index('\n## ') + 1
    open(CHANGELOG, 'w', encoding='utf-8').write(log[:i] + entry + log[i:])
    print('Added %d events.' % len(added))


if __name__ == '__main__':
    main()
