#!/usr/bin/env python3
import os, sys, argparse, re, time, datetime, psutil, socket, requests
from collections import Counter, defaultdict

# ---------------------------
# ANSI Colors
# ---------------------------
C = {
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
}

# ---------------------------
# ASCII banner with colors
# ---------------------------
BANNER = (
    C["CYAN"]
    + r"""
   ____          _      __  __                 _ 
  / ___|___   __| | ___|  \/  | ___   ___   __| |
 | |   / _ \ / _` |/ _ \ |\/| |/ _ \ / _ \ / _` |
 | |__| (_) | (_| |  __/ |  | | (_) | (_) | (_| |
  \____\___/ \__,_|\___|_|  |_|\___/ \___/ \__,_|
          CLI Tool for Mood-Driven Dev Insights
"""
    + C["RESET"]
)


# ---------------------------
# Utility: check file existence
# ---------------------------
def check_file(path):
    return os.path.isfile(path)


# ---------------------------
# Utility: read file safely
# ---------------------------
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except:
        return ""


# ---------------------------
# Utility: write to file
# ---------------------------
def write_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    except:
        pass


# ---------------------------
# Utility: system info
# ---------------------------
def sys_info():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "mem": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "boot": datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat(),
    }


# ---------------------------
# Utility: network info
# ---------------------------
def net_info():
    try:
        host = socket.gethostname()
        ip = socket.gethostbyname(host)
        return {"host": host, "ip": ip}
    except:
        return {"host": "?", "ip": "?"}


# ---------------------------
# Mood keywords
# ---------------------------
MOOD_WORDS = {
    "happy": ["success", "done", "great", "awesome", "good", "happy"],
    "sad": ["fail", "error", "bug", "issue", "sad", "bad"],
    "angry": ["angry", "wtf", "hate", "annoy", "frustrated"],
    "calm": ["ok", "fine", "stable", "smooth", "normal"],
}


def mood_score(text):
    counts = defaultdict(int)
    for mood, words in MOOD_WORDS.items():
        for w in words:
            counts[mood] += len(re.findall(r"\b" + re.escape(w) + r"\b", text, re.I))
    return dict(counts)


# ---------------------------
# Colorize mood output
# ---------------------------
def color_mood(ms):
    s = []
    for k, v in ms.items():
        col = (
            C["GREEN"]
            if k == "happy"
            else C["RED"] if k == "angry" else C["YELLOW"] if k == "sad" else C["BLUE"]
        )
        s.append(f"{col}{k}:{v}{C['RESET']}")
    return " | ".join(s)


# ---------------------------
# Scan files
# ---------------------------
def scan_files(paths):
    result = defaultdict(Counter)
    for p in paths:
        if check_file(p):
            txt = read_file(p)
            ms = mood_score(txt)
            result[p].update(ms)
    return result


# ---------------------------
# Watch dir real-time
# ---------------------------
def watch_dir(path, interval=5):
    seen = {}
    start = time.time()
    try:
        while True:
            files = []
            for root, _, fs in os.walk(path):
                for fn in fs:
                    files.append(os.path.join(root, fn))
            total = len(files)
            for i, fp in enumerate(files, 1):
                mtime = os.path.getmtime(fp)
                if fp not in seen or seen[fp] != mtime:
                    seen[fp] = mtime
                    txt = read_file(fp)
                    ms = mood_score(txt)
                    print(
                        f"{C['MAGENTA']}[{i}/{total}]{C['RESET']} {fp} => {color_mood(ms)}",
                        end="\r",
                    )
            time.sleep(interval)
    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\nStopped watching. Elapsed: {C['CYAN']}{elapsed:.2f}s{C['RESET']}")


# ---------------------------
# System stats
# ---------------------------
def cmd_sys():
    info = sys_info()
    net = net_info()
    print(f"{C['BOLD']}System Info:{C['RESET']}", info)
    print(f"{C['BOLD']}Network Info:{C['RESET']}", net)


# ---------------------------
# Analyze repo
# ---------------------------
def analyze_repo(path):
    stats = Counter()
    files = []
    for root, _, fs in os.walk(path):
        for fn in fs:
            if fn.endswith((".py", ".js", ".java", ".txt", ".md")):
                files.append(os.path.join(root, fn))
    total = len(files)
    start = time.time()
    for i, fp in enumerate(files, 1):
        txt = read_file(fp)
        ms = mood_score(txt)
        stats.update(ms)
        if i % 10 == 0 or i == total:
            print(f"{C['MAGENTA']}[{i}/{total}]{C['RESET']} Scanning {fp}...", end="\r")
    elapsed = time.time() - start
    print(
        f"\nRepo mood: {color_mood(stats)}\nTime taken: {C['CYAN']}{elapsed:.2f}s{C['RESET']}"
    )


# ---------------------------
# Fetch URL
# ---------------------------
def fetch_url(url):
    try:
        r = requests.get(url, timeout=5)
        txt = r.text[:1000]
        print(f"{C['CYAN']}Fetched:{C['RESET']} {url}")
        print(txt[:200].replace("\n", " "))
        ms = mood_score(txt)
        print("Mood:", color_mood(ms))
    except Exception as e:
        print(f"{C['RED']}Fetch error:{C['RESET']}", e)


# ---------------------------
# Save results
# ---------------------------
def save_results(path, data):
    write_file(path, str(data))
    print(f"Results saved to {C['GREEN']}{path}{C['RESET']}")


# ---------------------------
# CLI parser
# ---------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description="CodeMood CLI Tool: Analyze mood from code, repos, and logs",
        epilog="""Examples:
  python codemood.py scan file1.py file2.js
  python codemood.py watch ./src --interval 10
  python codemood.py sys
  python codemood.py repo ./project
  python codemood.py fetch https://example.com
  python codemood.py save results.txt "All good!"
""",
    )
    sub = ap.add_subparsers(dest="cmd")
    scan = sub.add_parser("scan", help="scan files")
    scan.add_argument("files", nargs="+")
    watch = sub.add_parser("watch", help="watch dir")
    watch.add_argument("path")
    watch.add_argument("--interval", type=int, default=5)
    sub.add_parser("sys", help="system info")
    repo = sub.add_parser("repo", help="analyze repo")
    repo.add_argument("path")
    fetch = sub.add_parser("fetch", help="fetch url")
    fetch.add_argument("url")
    save = sub.add_parser("save", help="save results")
    save.add_argument("path")
    save.add_argument("data")
    return ap.parse_args()


# ---------------------------
# Main entry
# ---------------------------
def main():
    print(BANNER)
    args = parse_args()
    if args.cmd == "scan":
        res = scan_files(args.files)
        print(color_mood(res))
    elif args.cmd == "watch":
        watch_dir(args.path, args.interval)
    elif args.cmd == "sys":
        cmd_sys()
    elif args.cmd == "repo":
        analyze_repo(args.path)
    elif args.cmd == "fetch":
        fetch_url(args.url)
    elif args.cmd == "save":
        save_results(args.path, args.data)
    else:
        print("No command. Use -h for help.")


if __name__ == "__main__":
    main()
