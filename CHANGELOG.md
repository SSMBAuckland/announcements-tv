# Changelog

All notable changes to the SSMB Announcements TV display (`index.html`) are recorded here, newest first.

## 2026-10-26 (pictures)
- **Pictures with an event:** an event can now show a picture in the Today card (`image`, a file in `images/`). Upright pictures (murtis, posters, portraits) stand on the right and fade into the card towards the text; wide ones fill the top of the card and fade to dark behind the text under them. The text keeps its sizes; the shlok gives way on picture days, and a picture that can't be loaded is left out (the display check reports it).
- **Colours from a poster:** an event's `palette` sets the day's colours (field, accent and label hues), so the screen can match the poster the admins shared. The field stays dark and the text light; a festival theme keeps its scenery.
- **Lalji Maharaj's Visit** (Sat 31 Oct): Lalji Maharaj's picture from the poster the admins sent (cropped to him, without the poster's text and logos) beside the event, and the poster's blue and maroon as the day's colours.
- Removed the purple placeholder photo layer (`background.svg`) added earlier today: it darkened every day, and pictures now go with their event instead.

## 2026-10-26 (photo background)
- **From the admin team (WhatsApp) — photo background:** the display now has a photo layer behind everything, with a dark gradient over it so event names, dates and times stay high-contrast. The picture was not available to us, so a plain purple placeholder (`background.svg`) is in place; add the real picture next to `index.html` and point the `.screen::after` url at it. Text and sizes are unchanged; no events added.

## 2026-10-26 (later)
- **From the admin team (WhatsApp) — Lalji Maharaj's Visit festive look** (Sat 31 Oct 2026 only): the day gets its own warm saffron-and-gold theme (`"theme": "lalji"`), a marigold toran along the top with faint rangolis behind, a gold double frame around the Today card, gold stars either side of the "Mandir Programme" label and a warm glow behind the event name. All text and sizes are unchanged.

## 2026-10-26
- **From the admin team (WhatsApp) — Lalji Maharaj's Visit:**
  - Added: 31 Oct Lalji Maharaj's Visit

## 2026-10-21 (later)
- **Sharad Poonam festive look** (Sun 25 Oct 2026, and 14 Oct 2027): the Today title becomes **"Happy Sharad Poonam!"**, and the moonlit blue theme gets its own scenery, drawn in code and kept faint behind the text: a white jasmine garland with pearl drops along the top, a large glowing full moon with twinkling stars, and crossed raas dandiyas over the Yamuna's ripples along the bottom.

## 2026-10-21
- **From the admin team (WhatsApp) — Sharad Purnima Raas:**
  - Added: 25 Oct Thaal and Chesta; 25 Oct Aarti and Nitya Niyam; 25 Oct Sharad Purnima Raas; 25 Oct Podhaniya; 25 Oct Prasad Rupi Bhojan

## 2026-10-21
- **From the admin team (WhatsApp) — Removed: Hello Haiku 1008:**
  - Removed: 20 Oct Hello Haiku 1008

## 2026-10-21
- **From the admin team (WhatsApp) — Hello Haiku 1008:**
  - Added: 20 Oct Hello Haiku 1008

## 2026-10-21
- **Groundwork for updates from WhatsApp** (not switched on yet). A new GitHub Action, *WhatsApp update*, will put announcements the admin team approves on WhatsApp onto the display. Plain event changes go through `scripts/apply_update.py` (no AI); festive themes and other changes are made by Claude Code. Every change is checked at 1920×1080 by `scripts/check_display.py` before it is published. No change to what the screen shows.

## 2026-10-20 (later)
- **Sat 7 Nov:** the programme item is renamed from "Hanuman Jayanti" to **Kali Chaudash** (6:45 PM onwards; Hanumanji Jeevan Akhyan; Pujan, Aarti & Chalisa Paath). The calendar's own "Kali Chaudash" entry is hidden that day so it isn't listed twice, and its festival message moves to the programme item. Kali Chaudash keeps the saffron Hanuman theme and scenery (also in 2027, where the calendar spells it "Kali Chaudas").

## 2026-10-20
- **Hanuman Jayanti, Diwali and Annakut programmes** added as "Mandir Programme" items:
  - **Sat 7 Nov:** Hanuman Jayanti, 6:45 PM onwards (Hanumanji Jeevan Akhyan; Pujan, Aarti & Chalisa Paath).
  - **Sun 8 Nov:** Lakshmi Poojan 6:00 – 7:00 PM, Thaal and Chesta 7:00 PM, Aarti, Nitya Niyam and Katha 7:30 PM, Deepotsav Aarti 8:00 PM. The calendar's "Laxmi Pujan" is hidden that day (marked `"hidden": true`, so the weekly sync won't add it back).
  - **Mon 9 Nov:** Annakut Aarti and Thaal 4:00 – 4:30 PM, Annakut Darshan 4:00 – 7:00 PM, Thaal, Chesta, Katha & Ashirwad Clips 6:30 – 7:30 PM, Aarti and Nitya Niyam 7:30 PM, Sneh Milan 7:45 PM (followed by Mahaprashad).
- **Festival scenery**, drawn in code (works offline, faint enough not to compete with text): Hanuman Jayanti — saffron theme, saffron flags across the top and faint mountains along the bottom; Diwali — marigold garland, a row of flickering diyas and a faint rangoli; Annakut — marigold garland, the Govardhan hill and rows of laddoo offerings. Hanuman Jayanti is a new themed festival (no countdown, so Diwali's countdown isn't displaced).
- The Shikshapatri shlok is hidden on these three days (`"hideShlok": true` on an event hides it for that day) so the programme gets the room.
- A programme of four or more items now uses the full width of the Today panel, with the day's festivals on one "Also today" line above it. "On now" sits beside the event name in timetable rows.

## 2026-10-19
- **Calendar sync:** added 1 new event from the Bhuj Mandir calendar:
  - 5 Nov 2026 Vaghbaras

## 2026-10-19
- **Weekly calendar sync.** A GitHub Action now checks the Bhuj Mandir Google Calendar every Monday at 6 am (NZ) and adds any new events, using the same filtering as the 2027 import. It only adds events (never edits or removes them), writes a changelog entry for what it added, and refreshes the website and TVs. It can also be run by hand from the Actions tab. Script: `scripts/sync_calendar.py`; workflow: `.github/workflows/calendar-sync.yml`.
- The Yodeck refresh workflow can now also be called by other workflows (needed because automatic commits don't trigger it).

## 2026-10-18
- **2027 events added** from the Bhuj Mandir "Australia and New Zealand Utsav" Google Calendar (278 entries, 3 Jan – 29 Dec 2027). Festival messages are reused where the same festival already had one (123 entries).
  - Left out, as with the 2026 list from the same calendar: daily/monthly observances (Pradosh Vrat, Masik Shivratri, Amas, Vrat ni Poonam), instructions for the pujaris ("Swing Shree Thakorji in the paranu…", "adorn Shree Thakorji in…"), astronomical notes ("Sun enters…", "Holashtak … at"), Snan/Kamurta notices and the individual daily Shraddh days (Shraddh Begins, Mahalay Ends and Sarvapitri Shraddh are kept).
  - Historical anniversaries ("Birth of Sadguru Brahmanand Swami", "Shree Hari gave diksha…") are included, with the Samvat year and place as a note, and are listed after the day's festivals.
  - "… Fast" is dropped from names (e.g. "Safala Ekadashi", "Shree Ramnavmi").
- New big festivals with their own colour theme and countdown: **Shree Swaminarayan Jayanti** and **Janmashtami**. Annkutotsav and Nutan Varsh are also recognised under the 2027 calendar's spellings ("Annakutotsav", "New Year begins").
- Very full days: if a day still doesn't fit at wall-legible sizes, the lowest-priority items are replaced by a "+ N more today" line (or "+ N more" in Upcoming) instead of being cut off.
- Long festival names in the countdown strip (e.g. "Prabodhini Ekadashi") shrink to fit.

## 2026-10-14
- Fixed misaligned layout when the Mandal programme has only one item beside festivals (e.g. 14 Oct "Special Sabha: Seva" with Vinayaki Choth): it was drawn as a one-row timetable, squeezing the name into three lines with the time out of line. A single item now stacks — heading, large name, time — all on one left edge. Timetable rows are used only when there are two or more timed items.

## 2026-10-13
- **Readable from across the hall.** On the TV, text never shrinks below wall-legible minimums: event names 56px (44px for festivals in the side column), today's times 40px, Upcoming names 38–42px and times 30–32px, notes / festival message / "Earlier today" / shlok 28–30px, small capital labels 22–24px (previously some text went as small as 13px). Phones keep their own sizing.
- When a day is too full to fit at those sizes, the least important content gives way instead of text shrinking: the festival message and introductions on the Today panel, notes and source labels in Upcoming.
- **Calmer, clearer layout:**
  - Smaller clock (196 → 140px) and slimmer header, so the events get the space. The date is plain text on the right (it still opens the preview calendar when clicked).
  - Pills removed: "Mandal Santos Schedule", "Tomorrow", "Also today" and the seconds are now small gold capitals or plain text; no more card inside a card on busy days (a hairline divides the programme and festival columns).
  - Any day with two or more timed events shows a timetable (time | event) with the times lined up in one column; "onwards" sits beneath its time. A single event stays large and centred.
  - The event in progress gets a soft highlight across its row, with a glowing dot and "ON NOW" under the time.
  - "Today at the Mandir" and "Upcoming Events" titles have a fine gold rule instead of an underline.
  - The festival countdown is a compact strip: "8 days to go │ Countdown to Dashera".
- Bigger header and Upcoming text (weekday 54px, date 38px, Upcoming names up to 62px).
- Long shloks are split into shorter parts (about 180 characters at most) so every part fits the band at the larger size.

## 2026-10-10
- **Bigger events on busy days.** When today has both Mandal Santos Schedule items and festivals, the Today panel now splits in two:
  - **Left (two-thirds):** the Mandal programme in its own highlighted card, laid out as a timetable (time on the left, event on the right) under a gold "Mandal Santos Schedule" heading. "Earlier today" sits at the bottom of this card.
  - **Right (one-third):** festivals under an "Also today" label, with the festival message. Festival names are never more than 80% of the programme's size, so the programme always leads.
- On busy days (two columns, or three or more events still to come) the Shikshapatri band is slimmer (164px instead of 236px, text up to 30px instead of 40px), giving the events more room. Quiet days keep the larger shlok.
- Slightly larger maximum sizes for days with 2–5 events.
- Event sizing now also checks width, so a long word such as "Bhojan/Ahar" shrinks to fit instead of running off the edge.

## 2026-10-09
- Added "Q&A with Santos, 7:00 PM onwards" to Saturday 10 Oct.
- **Live event status on the Today panel:** the event in progress gets an "On now" tag beside its time, and finished events move out of the main list into a small "✓ Earlier today" line underneath, so the next event is always the big one. When everything with a time has finished, the panel says "Today's programme is complete – Thank you for joining us". Events without a time (festivals) are never marked finished. An event with only a start time is treated as running until the next timed event (at most 3 hours, or 90 minutes if it's the last one); "onwards" runs to the end of the day.
- Previews can now set a time of day too: `?previewDate=2026-10-10&previewTime=19:30`.
- Saturday 10 Oct programme: Mahapooja (3:30 AM), Anushthan (6:00 AM, as per the schedule) and Aarti, Nitya Niyam & Katha (7:00 AM). Replaces the earlier "Anushthan & Q&A with Santos, 7:45 – 9:00 AM" entry.
- The "Mandal Santos Schedule" label (and any other source label) now appears once above a run of events that share it, instead of on every line.
- The festival countdown card now hides itself when tomorrow's events would otherwise be squeezed too small to read (or cut off).

## 2026-10-08
- Added the full 9 Oct evening programme: Thaal, Chesta, Aarti & Nitya Niyam (6:15 – 7:00 PM), Mahaprashad (7:00 – 8:00 PM) and Katha Parayan – Day 5 (8:00 – 9:30 PM). Fixed the old note that put Mahaprashad after the Katha.
- Added subtle ambient animations: the background glow slowly drifts, a few soft sparks in the day's accent colour float upwards, a gentle halo breathes behind the crest, and a band of light passes across the festival countdown card every few seconds. Only transform/opacity are animated so the Yodeck player stays smooth, and all of it switches off for viewers who ask their device for reduced motion.
- Fixed missing spaces in shlok 206 ("Dharma (virtue), Artha (wealth), Kama (pleasure) and Moksha (salvation)"), which was being cut off on phones.

## 2026-10-05

### Added
- **Festival messages:** on festival days, the festival's short message now appears in italics under today's events (one per day, the main festival's own message first).
- **More upcoming days:** the Upcoming panel now shows up to 4 upcoming days (the next one in full, the rest as compact rows) when they fit, and the title changes to "Upcoming Events".
- **Festival countdown:** for the 21 days before Navratri, Dashera, Sharad Poonam, Diwali, Annkutotsav, Nutan Varsh and Prabodhini Ekadashi, a "Countdown to …" card appears at the bottom of the Upcoming panel. It is hidden when the festival is already listed in the panel.
- **Festival themes:** each of those festivals gets its own colour theme on the day. Navratri, Dashera, Diwali and Nutan Varsh also replace the "Today at the Mandir" title with a greeting (e.g. "Happy Diwali!", "Nutan Varshabhinandan!"). The festival list is `FESTIVALS` in `index.html`.

- **Festivals listed first:** within each day, big festivals come first (e.g. Diwali before Laxmi Pujan and Chopda Pujan), then other festivals, then scheduled programmes such as the Mandal Santos Schedule.

### Fixed
- Removed the duplicate "Chopada Poojan" (8 Nov, same as Chopda Pujan) and the second "Gita Jayanti" (20 Dec).
- Removed a double space in "HH 1008 Acharya Shree Koshalendra Prasadji Maharaj".
- Shloks that share one translation (3–6, 49–54, 77–78, 81–82, 93–95, 101–102, 109–110, 153–154, 175–176, 194–195) are now shown once, labelled e.g. "Shikshapatri, Shloks 3–6" (212 entries → 195).
- Fixed broken words in shlok text ("rosaries", "non-violence", "households", "marriage-connections", "sensory-organs") and removed the "(Vide page 5 SHIKSHAPATRI ARTHA DEEPIKA)" note from shlok 1.

## 2026-10-04

### Changed
- Rebuilt the dashboard layout and rendering script (file size cut from ~394 KB to ~236 KB).
- Fonts (Philosopher and others) are now embedded directly in the page instead of loaded from Google Fonts, so the screen no longer needs an external network request to show the correct typography.
- Header now shows the Mandir crest with the name "Shree Swaminarayan Mandir Bhuj — Auckland, New Zealand", alongside the clock (with seconds) and date card.
- "Today at the Mandir" panel and "Upcoming Event" panel reworked, with new automatic layout fitting for long notes and portrait screens.
- Rotating shlok band now paginates long shloks and shows its source.
- Daily colour theme generation rewritten.
- Page language set to `en-NZ`.

### Events
- **4 Oct 2026:** the separate "Mahapooja" (6:00 AM) and "Pothi Yatra & Raas" (5:15 PM onwards) entries are merged into a single "Mahapooja & Raas" entry, 7:45 – 9:00 AM, "Followed by Pothi Yatra & Raas".
- **9 Sep 2026 (Bal Krishna Chhathi):** added an introduction message.

## 2026-10-03
- Updated Mahapooja and Raas details.

## 2026-09-29
- Reverted the display to the previous Claude-generated version.
