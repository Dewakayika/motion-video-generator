"""ElevenLabs voiceover for the explainers: the video timing follows the voice.
Set ELEVENLABS_API_KEY in the environment first (never on the command line or in a file).

Run from the repo root:
  1. python tools/vo.py gen projects/<project>/<page>.html [--voice ID] [--fix fixes.json]
       One clip per CAP caption at natural speed (vo/NN.mp3, cached in vo/clips.json, so unchanged lines are
       not generated again). Where a clip is longer than the gap to the next caption, the timeline is stretched:
       the anchors are written to `const WARP=[...]` in the HTML and the page plays that stretch slower.
  2. python tools/render.py projects/<project>/<page>.html      (re-render with the new timing)
  3. python tools/vo.py mux projects/<project>/<page>.html projects/<project>/output/<page>-1080p.mp4
       Places every clip at its retimed caption start and writes output/<page>-vo-1080p.mp4 and <page>-vo.wav.

--fix: JSON {"caption text": "spoken text"} for lines that should be read differently from how they are shown.
"""
import argparse, html, json, os, pathlib, re, subprocess, sys, urllib.request

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
DEFAULT_VOICE = "IKne3meq5aSn9XLyUdCD"  # Charlie, Australian English
MODEL = "eleven_multilingual_v2"
SPEED = 1.0
GAP = 0.35   # pause after a clip before the next caption
TAIL = 0.8   # hold after the last clip

def captions(page):
    src = page.read_text(encoding="utf-8")
    dur = float(re.search(r"const DUR=([\d.]+)", src).group(1))
    block = re.search(r"const CAP=\[(.*?)\];", src, re.S).group(1)
    caps = [(float(a), float(b), t) for a, b, t in re.findall(r'\[([\d.]+),([\d.]+),"((?:[^"\\]|\\.)*)"\]', block)]
    return src, dur, caps

def spoken(text, fixes):
    t = html.unescape(re.sub(r"<[^>]+>", "", text)).replace("“", '"').replace("”", '"')
    return fixes.get(t, t)

def length(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())

def tts(text, voice, key, prev, nxt):
    body = {"text": text, "model_id": MODEL, "previous_text": prev, "next_text": nxt,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True, "speed": SPEED}}
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def gen(a):
    key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("ELEVENLABS_API_KEY is not set")
    page = pathlib.Path(a.page)
    fixes = json.loads(pathlib.Path(a.fix).read_text(encoding="utf-8")) if a.fix else {}
    src, dur, caps = captions(page)
    if "const WARP=" not in src:
        sys.exit(f"{page.name} has no `const WARP=[]` (retiming support): copy it from templates/explainer/explainer.html")
    vo = page.parent / "vo"; vo.mkdir(exist_ok=True)
    cache_file = vo / "clips.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    lines = [spoken(t, fixes) for _, _, t in caps]
    lens, chars = [], 0
    for i, text in enumerate(lines):
        out = vo / f"{i:02d}.mp3"
        hit = cache.get(f"{i:02d}")
        if not (hit and hit["text"] == text and hit["voice"] == a.voice and hit["speed"] == SPEED and out.exists()):
            prev, nxt = " ".join(lines[max(0, i - 2):i]), " ".join(lines[i + 1:i + 2])
            out.write_bytes(tts(text, a.voice, key, prev, nxt))
            chars += len(text)
            cache[f"{i:02d}"] = {"text": text, "voice": a.voice, "speed": SPEED}
        cache[f"{i:02d}"]["len"] = round(length(out), 3)
        lens.append(cache[f"{i:02d}"]["len"])
    cache_file.write_text(json.dumps(cache, indent=1), encoding="utf-8")

    # anchors: every caption start moves later if the voice before it needs more room
    warp, new = [[0, 0]], 0.0
    for i, (start, _, _) in enumerate(caps):
        if i == 0:
            new = start
        else:
            new = warp[-1][1] + max(start - caps[i - 1][0], lens[i - 1] + GAP)
        warp.append([start, round(new, 3)])
    warp.append([dur, round(new + max(dur - caps[-1][0], lens[-1] + TAIL), 3)])
    warp = [w for k, w in enumerate(warp) if k == 0 or w[0] > warp[k - 1][0]]
    stretched = any(abs((w[1] - warp[k - 1][1]) - (w[0] - warp[k - 1][0])) > 1e-3 for k, w in enumerate(warp) if k)
    value = json.dumps(warp if stretched else [], separators=(",", ":"))
    page.write_text(re.sub(r"const WARP=\[.*?\];", f"const WARP={value};", src, count=1, flags=re.S), encoding="utf-8")
    for i, (start, _, _) in enumerate(caps):
        print(f"{i:02d} {start:6.1f}s → {warp[i + 1][1]:6.1f}s  {lens[i]:4.2f}s  {lines[i][:70]}")
    print(f"\n{chars} characters generated · duration {dur:.1f}s → {warp[-1][1]:.1f}s · WARP written to {page.name}")
    print(f"Next: python tools/render.py {page.as_posix()}  then  python tools/vo.py mux {page.as_posix()} {(page.parent / 'output' / (page.stem + '-1080p.mp4')).as_posix()}")

def mux(a):
    page, video = pathlib.Path(a.page), pathlib.Path(a.video)
    src, dur, caps = captions(page)
    warp = json.loads(re.search(r"const WARP=(\[.*?\]);", src, re.S).group(1)) or [[0, 0], [dur, dur]]
    def rewarp(t):
        for (x0, y0), (x1, y1) in zip(warp, warp[1:]):
            if t <= x1:
                return y0 + (y1 - y0) * max(0, t - x0) / (x1 - x0)
        return warp[-1][1]
    out_dur = warp[-1][1]
    if abs(length(video) - out_dur) > 1.5:
        sys.exit(f"{video.name} is {length(video):.1f}s but the retimed page is {out_dur:.1f}s: re-render it first")
    vo = page.parent / "vo"
    inputs, chains = [], []
    for i, (start, _, _) in enumerate(caps):
        inputs += ["-i", str(vo / f"{i:02d}.mp3")]
        ms = int(rewarp(start) * 1000)
        chains.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[a{i}]")
    mix = ";".join(chains) + ";" + "".join(f"[a{i}]" for i in range(len(caps))) + \
          f"amix=inputs={len(caps)}:normalize=0,apad,atrim=0:{out_dur},loudnorm=I=-16:TP=-1.5:LRA=11[v]"
    stem = video.stem.replace("-1080p", "")
    wav = video.with_name(stem + "-vo.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", mix, "-map", "[v]", "-ar", "48000", str(wav)], check=True)
    out = video.with_name(stem + "-vo-1080p.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print(f"wrote {out}\nwrote {wav}")

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
g = sub.add_parser("gen"); g.add_argument("page"); g.add_argument("--voice", default=DEFAULT_VOICE); g.add_argument("--fix")
m = sub.add_parser("mux"); m.add_argument("page"); m.add_argument("video")
a = ap.parse_args()
gen(a) if a.cmd == "gen" else mux(a)
