import json, re, subprocess, webbrowser
import tkinter as tk
from collections import Counter
from datetime import datetime, date, timedelta
from html import escape
from pathlib import Path

# ---------------- storage ----------------
HOME = Path.home() / "devlog"
HOME.mkdir(exist_ok=True)
POSTS, CONFIG, SITE = HOME / "posts.jsonl", HOME / "config.json", HOME / "site"

if not CONFIG.exists():
    CONFIG.write_text(json.dumps({
        "name": "your_name",
        "tagline": "building things, breaking things",
        "code_folders": [str(Path.home() / "code")],
        "hide_repos": [],
        "links": {"github": "https://github.com/your_username"},
    }, indent=2))
cfg = json.loads(CONFIG.read_text())

BG, FG, DIM, BOX, GREEN = "#0c0c0c", "#ffb000", "#7a5500", "#1a1a1a", "#33ff66"
FONT = ("Courier New", 11)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
EXT_LANG = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".jsx": "React",
            ".tsx": "React", ".java": "Java", ".c": "C", ".cpp": "C++", ".go": "Go",
            ".rs": "Rust", ".html": "HTML", ".css": "CSS", ".rb": "Ruby", ".kt": "Kotlin",
            ".swift": "Swift", ".php": "PHP", ".sh": "Shell", ".dart": "Dart", ".sql": "SQL"}

# ---------------- tech traces ----------------
def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=10, creationflags=NO_WINDOW)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""

def find_repos():
    found = set()
    for folder in cfg["code_folders"]:
        root = Path(folder).expanduser()
        for pattern in (".git", "*/.git", "*/*/.git"):
            found.update(p.parent for p in root.glob(pattern))
    return sorted(r for r in found if r.name not in cfg.get("hide_repos", []))

def scan_repo(repo):
    args = ["log", "--pretty=format:%ad\t%s", "--date=format:%Y-%m-%d %H:%M"]
    me = git(repo, "config", "user.email").strip()
    if me:
        args.append(f"--author={me}")
    commits = [l.split("\t", 1) for l in git(repo, *args).splitlines() if "\t" in l]
    langs = Counter(EXT_LANG[s] for f in git(repo, "ls-files").splitlines()
                    if (s := Path(f).suffix.lower()) in EXT_LANG)
    return {"name": repo.name, "commits": commits, "langs": langs}

def load_posts():
    posts = []
    if POSTS.exists():
        for line in POSTS.read_text(encoding="utf-8").splitlines():
            try:
                posts.append(json.loads(line))
            except ValueError:
                pass
    return posts

state = {"posts": load_posts(), "projects": [], "tab": "log"}

def sorted_projects():
    return sorted(state["projects"], key=lambda p: p["commits"][0][0] if p["commits"] else "",
                  reverse=True)

def timeline():
    items = [(p["t"], "post", p["body"]) for p in state["posts"]]
    for pr in state["projects"]:
        items += [(t, "commit", f"{pr['name']}: {m}") for t, m in pr["commits"][:200]]
    return sorted(items, key=lambda x: x[0], reverse=True)[:300]

def stats():
    commits = [t for p in state["projects"] for t, _ in p["commits"]]
    stamps = commits + [p["t"] for p in state["posts"]]
    days = {t[:10] for t in stamps}
    d = date.today()
    if d.isoformat() not in days:
        d -= timedelta(days=1)
    streak = 0
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    return {"since": min(stamps, default="----------")[:10], "commits": len(commits),
            "posts": len(state["posts"]), "repos": len(state["projects"]), "days": len(days),
            "streak": streak, "langs": sum((p["langs"] for p in state["projects"]), Counter()),
            "tags": Counter(t.lower() for p in state["posts"] for t in p["tags"])}

def bars(counter, n=6, width=12):
    total = sum(counter.values()) or 1
    return [(k, "█" * max(1, round(width * v / total)), round(100 * v / total))
            for k, v in counter.most_common(n)]

# ---------------- views ----------------
def log_lines():
    out = []
    for t, kind, text in timeline():
        if kind == "post":
            out += [(f"[{t}]\n", "dim"), (text + "\n\n", None)]
        else:
            out += [(f"[{t}] ", "dim"), ("git> ", "git"), (text + "\n\n", "dim")]
    return out or [("nothing yet. write something below.\n", "dim")]

def project_lines():
    out = []
    for p in sorted_projects():
        langs = ", ".join(l for l, _ in p["langs"].most_common(3)) or "?"
        last = p["commits"][0][0] if p["commits"] else "never"
        out += [(f"> {p['name']}\n", "head"),
                (f"  {len(p['commits'])} commits · {langs}\n  last: {last}\n\n", "dim")]
    return out or [("no repos found. edit code_folders in\n~/devlog/config.json\n", "dim")]

def stat_lines():
    s = stats()
    out = [("SYSTEM PROFILE\n\n", "head"),
           (f"coding since  {s['since']}\nrepos         {s['repos']}\n"
            f"commits       {s['commits']}\nposts         {s['posts']}\n"
            f"active days   {s['days']}\nstreak        {s['streak']} day(s)\n\n", None),
           ("LANGUAGES\n\n", "head")]
    out += [(f"{k:<11}{b} {p}%\n", None) for k, b, p in bars(s["langs"])]
    out += [("\nTHINGS I WRITE ABOUT\n\n", "head"),
            ("  ".join(f"#{t}({c})" for t, c in s["tags"].most_common(12)) or "no tags yet", "dim")]
    return out

def render(tab=None):
    state["tab"] = tab or state["tab"]
    lines = {"log": log_lines, "projects": project_lines, "stats": stat_lines}[state["tab"]]()
    view.config(state="normal")
    view.delete("1.0", "end")
    for text, tag in lines:
        view.insert("end", text, tag or ())
    view.config(state="disabled")
    for name, lbl in tab_labels.items():
        lbl.config(fg=FG if name == state["tab"] else DIM)

# ---------------- actions ----------------
def post(e=None):
    body = entry.get("1.0", "end").strip()
    if body:
        p = {"t": datetime.now().strftime("%Y-%m-%d %H:%M"), "body": body,
             "tags": re.findall(r"#(\w[\w+-]*)", body)}
        with POSTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(p) + "\n")
        state["posts"].append(p)
        entry.delete("1.0", "end")
        render("log")
    return "break"

def rescan(e=None):
    view.config(state="normal")
    view.delete("1.0", "end")
    view.insert("end", "scanning repos...\n", "dim")
    view.config(state="disabled")
    root.update_idletasks()
    state["projects"] = [scan_repo(r) for r in find_repos()]
    render()

def toggle_top(e=None):
    root.attributes("-topmost", not root.attributes("-topmost"))
    return "break"

def export(e=None):
    s = stats()
    SITE.mkdir(exist_ok=True)
    links = " · ".join(f'<a href="{escape(u)}">{escape(k)}</a>' for k, u in cfg.get("links", {}).items())
    lang_rows = "\n".join(f"{k:<11}{b} {p}%" for k, b, p in bars(s["langs"], 8, 24))
    projects = "".join(
        f'<div class="card"><b>&gt; {escape(p["name"])}</b><br><span class="dim">'
        f'{len(p["commits"])} commits · {escape(", ".join(l for l, _ in p["langs"].most_common(3)) or "?")}'
        f' · last {p["commits"][0][0][:10] if p["commits"] else "never"}</span></div>'
        for p in sorted_projects())
    feed = "".join(
        f'<div class="entry"><span class="dim">[{t}]</span> '
        + ('<span class="git">git&gt;</span> ' if k == "commit" else "")
        + escape(x).replace("\n", "<br>") + "</div>"
        for t, k, x in timeline())
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(cfg['name'])}</title><style>
body{{background:#0c0c0c;color:#ffb000;font:15px/1.6 "Courier New",monospace;max-width:760px;margin:40px auto;padding:0 20px}}
body::after{{content:"";position:fixed;inset:0;pointer-events:none;background:repeating-linear-gradient(transparent 0 2px,rgba(0,0,0,.25) 2px 4px)}}
a{{color:#ffd27a}} .dim{{color:#7a5500}} .git{{color:#33ff66}}
h1{{margin:0}} h1::after{{content:"█";animation:b 1s steps(1) infinite}} @keyframes b{{50%{{opacity:0}}}}
h2{{border-bottom:1px dashed #7a5500;margin-top:40px;font-size:15px}}
.card,.entry{{margin:12px 0}} pre{{margin:0;font:inherit}}
</style></head><body>
<h1>~/{escape(cfg['name'])}</h1><div class="dim">{escape(cfg['tagline'])}</div><p>{links}</p>
<h2>SYSTEM PROFILE</h2><pre>coding since  {s['since']}
repos         {s['repos']}
commits       {s['commits']}
posts         {s['posts']}
active days   {s['days']}
streak        {s['streak']} day(s)</pre>
<h2>LANGUAGES</h2><pre>{escape(lang_rows)}</pre>
<h2>PROJECTS</h2>{projects}
<h2>LOG</h2>{feed}
<p class="dim">generated {datetime.now():%Y-%m-%d %H:%M}</p></body></html>"""
    (SITE / "index.html").write_text(html, encoding="utf-8")
    webbrowser.open((SITE / "index.html").as_uri())

# ---------------- window ----------------
root = tk.Tk()
root.title("devlog")
root.configure(bg=BG)
W = 340
root.geometry(f"{W}x{root.winfo_screenheight() - 80}+{root.winfo_screenwidth() - W}+0")

tk.Label(root, text=f"~/{cfg['name']}", bg=BG, fg=FG, font=(FONT[0], 13, "bold")).pack(pady=(10, 0))
tk.Label(root, text=cfg["tagline"], bg=BG, fg=DIM, font=(FONT[0], 9)).pack()

tabs = tk.Frame(root, bg=BG)
tabs.pack(fill="x", padx=8, pady=8)
tab_labels = {}
for name in ("log", "projects", "stats"):
    lbl = tk.Label(tabs, text=f"[{name.upper()}]", bg=BG, fg=DIM, font=FONT, cursor="hand2")
    lbl.pack(side="left", padx=(0, 4))
    lbl.bind("<Button-1>", lambda e, n=name: render(n))
    tab_labels[name] = lbl
exp = tk.Label(tabs, text="[EXPORT]", bg=BG, fg=GREEN, font=FONT, cursor="hand2")
exp.pack(side="right")
exp.bind("<Button-1>", export)

view = tk.Text(root, bg=BG, fg=FG, font=FONT, wrap="word", bd=0, highlightthickness=0,
               padx=12, state="disabled", cursor="arrow")
view.tag_config("dim", foreground=DIM)
view.tag_config("git", foreground=GREEN)
view.tag_config("head", font=(FONT[0], 11, "bold"))
view.pack(fill="both", expand=True)

entry = tk.Text(root, height=4, bg=BOX, fg=FG, insertbackground=FG, font=FONT,
                wrap="word", bd=0, padx=8, pady=6)
entry.pack(fill="x", padx=8, pady=(6, 2))
entry.focus_set()
tk.Label(root, text="ctrl+enter post · #tags · f5 rescan · ctrl+t pin",
         bg=BG, fg=DIM, font=(FONT[0], 9)).pack(pady=(0, 8))

entry.bind("<Control-Return>", post)
root.bind("<F5>", rescan)
root.bind("<Control-t>", toggle_top)
root.bind("<Control-e>", export)

render("log")
root.after(300, rescan)
root.mainloop()