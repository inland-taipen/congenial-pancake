# devlog

A tiny retro desktop widget that turns my coding life into a living timeline: my thoughts, my git commits, my projects, and my languages, all in one amber-on-black terminal window docked to the side of my screen.

It's part journal, part portfolio, part "metaverse of me." I write posts, and it automatically collects my tech traces from every git repo on my machine. With one click, it exports everything as a static retro portfolio page.

![devlog screenshot](screenshot.png)

## Features

- **Write anytime.** Quick posts with timestamps. Add `#tags` to categorize them (`finally fixed the race condition #python #debugging`).
- **Automatic tech traces.** Scans your local git repos and pulls in your commits and the languages you use.
- **Three views:**
  - `[LOG]` shows your posts and git commits merged into one timeline, newest first.
  - `[PROJECTS]` shows every repo, with commit count, top languages, and last activity.
  - `[STATS]` shows your "system profile": coding since, total commits, active days, current streak, language bars, and favorite tags.
- **Export to a portfolio page.** Generates a single self-contained `index.html` with CRT scanlines and a blinking cursor, ready for GitHub Pages.
- **Featherweight.** About 20–30 MB RAM, 0% CPU when idle, and no server, database, or dependencies. Git is only scanned at startup or on rescan.

## Requirements

- Python 3.8+ with Tkinter
- Git

## Installation (macOS)

Homebrew's Python doesn't include Tkinter by default, so install it separately (match your Python version):

```bash
brew install python-tk@3.14
```

Clone or download this folder, then run:

```bash
python3.14 devlog.py
```

> Use `python3.14` rather than `python3`. On macOS, `python3` may point to Apple's built-in Python, which uses a deprecated Tk that renders poorly.

## Configuration

On first run, devlog creates `~/devlog/config.json`. Edit it, then restart the widget:

```json
{
  "name": "anika",
  "tagline": "building things, breaking things",
  "code_folders": ["~/RandomIdeas"],
  "hide_repos": [],
  "links": {
    "github": "https://github.com/your_username",
    "linkedin": "https://linkedin.com/in/your_handle"
  }
}
```

| Key | What it does |
|---|---|
| `name` | Shown as `~/name` in the header and on the exported page |
| `tagline` | Subtitle under your name |
| `code_folders` | Folders to scan for git repos (searched up to 2 levels deep) |
| `hide_repos` | Repo folder names to exclude everywhere, e.g. work or client projects |
| `links` | Shown on the exported portfolio page |

## Usage

| Shortcut | Action |
|---|---|
| `⌘ + Enter` / `Ctrl + Enter` | Publish a post |
| `⌘ + R` / `F5` | Rescan git repos |
| `⌘ + T` / `Ctrl + T` | Toggle always-on-top |
| `⌘ + E` / `Ctrl + E` | Export portfolio page |

Click the `[LOG]`, `[PROJECTS]`, and `[STATS]` tabs to switch views, or `[EXPORT]` to generate the site.

## Where data lives

Everything is stored in `~/devlog/`, separate from the code, so you can move or update the script without losing anything.

```
~/devlog/
├── config.json      # your settings
├── posts.jsonl      # your posts, one JSON object per line
└── site/
    └── index.html   # exported portfolio page
```

Posts are plain JSON Lines, so they're easy to back up, grep, or migrate:

```json
{"t": "2026-10-13 15:11", "body": "Hi I am Anika", "tags": []}
```

## Launch at login (macOS)

Create `~/Library/LaunchAgents/com.anika.devlog.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST