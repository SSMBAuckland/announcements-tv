# Notes for Claude

- **Always commit and push straight to `main`.** Do not create feature branches or pull requests; `main` is what goes live (GitHub Pages + the Yodeck refresh workflow).
- Before pushing, open `index.html` in headless Chromium (use `?previewDate=YYYY-MM-DD` to check specific days) and confirm there are no page errors and the layout fits at 1920×1080.
- Add an entry to the top of `CHANGELOG.md` for every change to the display.
- **The display hangs on a wall and is read from across the hall — legibility from a distance comes first.** Event names and times are always the largest, most prominent text. On the TV (1920×1080 canvas) text never goes below: event names 56px (festival side column 44px), today's times 40px, Upcoming names 38–42px and times 30–32px, everything else 28px, small-capital labels 22–24px. These floors are the `--min-*` variables on `body.tv-canvas`. When a day is too full, drop secondary content (festival message, notes, source labels) instead of shrinking text below the floors. Keep shlok parts short enough to fit the band at these sizes.
