# 🕒 SSMB Announcements TV

The live event display for the TV screens at **Shree Swaminarayan Mandir Bhuj – Auckland**.

**Live page:** [ssmbauckland.github.io/announcements-tv](https://ssmbauckland.github.io/announcements-tv/)

The whole display is one file, `index.html`. When it changes on `main`, the website updates automatically and the TVs are told to reload.

---

## 📋 Contents
1. [What's on the screen](#-whats-on-the-screen)
2. [How updates reach the TVs](#-how-updates-reach-the-tvs)
3. [Previewing a date](#-previewing-a-date)
4. [Adding or changing events](#-adding-or-changing-events)
5. [Publishing a change](#-publishing-a-change)
6. [Troubleshooting](#-troubleshooting)
7. [Changelog](#-changelog)

---

## 📺 What's on the screen

| Area | What it shows |
|---|---|
| **Header** | Mandir crest and name, a large clock (with seconds), and today's date. |
| **Today at the Mandir** | Today's events with times and notes, and the festival's message. When there are both Mandal programme items and festivals, the programme is shown as a timetable card on the left and festivals on the right ("Also today"). The event in progress is tagged "On now"; finished ones move to a small "Earlier today" line. On big festivals the title becomes a greeting, e.g. "Happy Diwali!". |
| **Shlok band** | A Shikshapatri shlok that changes every 2 minutes. Long shloks are shown in parts. |
| **Upcoming Events** | The next day with events in full, plus up to three more days as short rows. |
| **Festival countdown** | For the 21 days before a big festival, a "Countdown to …" card. |

Each day gets its own colour theme, and big festivals have their own colours. Festivals are listed first within each day, then scheduled programmes.

The page is self-contained (fonts and images are built in), so it works without loading anything else.

---

## 🔄 How updates reach the TVs

```
Edit index.html on main  →  GitHub Pages updates the website  →  GitHub Action tells Yodeck to reload the screens
```

The action is `.github/workflows/refresh-yodeck.yml`. It runs on every push to `main` and needs the `YODECK_API_KEY` repository secret. It usually finishes within about a minute; you can watch it in the **Actions** tab.

---

## 👀 Previewing a date

To see how the screen will look on any day:

* **Click the date card** (top right) on the live page to open the preview calendar, or
* Add `?previewDate=YYYY-MM-DD` to the address, e.g.
  [`…/announcements-tv/?previewDate=2026-11-08`](https://ssmbauckland.github.io/announcements-tv/?previewDate=2026-11-08)
* Add `&previewTime=HH:MM` (24-hour) to see which events show as "On now" or "Earlier today" at that time, e.g. `?previewDate=2026-10-10&previewTime=19:30`

Previews only affect your browser; the TVs always show today.

---

## ✏️ Adding or changing events

Events live in the `EVENTS` list near the top of the `<script>` section in `index.html`. Each event is one line:

```js
{"date": "8/11/2026", "event": "Diwali", "time": "7:00 PM", "note": "Aarti • Fireworks", "quote": "May the light of bhakti…", "progress": false},
```

| Field | Required | Meaning |
|---|---|---|
| `date` | ✅ | Day/month/year, e.g. `8/11/2026`. |
| `event` | ✅ | Name shown on screen. |
| `time` | | Shown under the name, e.g. `7:45 – 8:45 PM`. |
| `note` | | Extra lines; separate lines with ` • `. |
| `source` | | Small label above the name, e.g. `Mandal Santos Schedule`. |
| `quote` | | Short festival message shown under today's events. |
| `intro` | | A longer introduction shown under the event name. |
| `progress` | | Leave as `false` unless told otherwise. |

**Big festivals** (countdown, colour theme and greeting) are set in the `FESTIVALS` list. The `event` there must match the event name exactly.

> 💡 **Tip:** when only events change, edit just the `EVENTS` list rather than pasting a whole new file. Pasting a full AI-generated file can silently undo earlier fixes.

---

## 🚀 Publishing a change

> ⚠️ The file must be named exactly **`index.html`** (all lowercase) and stay in the top folder.

### Method A: Edit in GitHub (recommended)
1. Open **`index.html`** in this repository and click the **pencil icon** (✏️).
2. Make your change (or select all, delete, and paste the full new code).
3. Click **Commit changes…**, then **Commit changes** again.

### Method B: Upload a file
1. Rename the file on your computer to **`index.html`**.
2. In this repository, click **Add file → Upload files** and drop it in.
3. Click **Commit changes**.

Then:
1. Open the [live page](https://ssmbauckland.github.io/announcements-tv/) after a minute or two and check it looks right.
2. Add a line to [CHANGELOG.md](CHANGELOG.md) describing what changed.

---

## 🛠️ Troubleshooting

| Problem | What to do |
|---|---|
| Website hasn't changed | Wait 2–3 minutes and hard-refresh (`Ctrl + Shift + R` / `Cmd + Shift + R`). Check the **Actions** tab for a failed run. |
| Website is right but a TV isn't | Reload the player from the Yodeck dashboard, or unplug the Yodeck box behind the TV, wait **10 seconds**, and plug it back in. |
| Blank page or error | The file was probably cut off when pasting. Check it is named `index.html` and the full code was pasted, or restore the previous version from the commit history. |
| "No further events are listed yet" | The `EVENTS` list has run out; add the next set of dates. |
| Yodeck action fails | Check the `YODECK_API_KEY` secret under **Settings → Secrets and variables → Actions**. |

---

## 📝 Changelog

All changes to the display are recorded in **[CHANGELOG.md](CHANGELOG.md)**, newest first. Please add an entry whenever you publish a new `index.html`.
