# Changelog

All notable changes to the SSMB Announcements TV display (`index.html`) are recorded here, newest first.

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
