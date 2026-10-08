"""
Urdu audio -> transcript CSV.

Put audio clips in the  audios/  folder, then run:   python transcribe_audios.py
(optionally:  python transcribe_audios.py --start 441)

For every batch it:
  1. drops clips shorter than 45 s
  2. transcribes the rest in Urdu (faster-whisper, offline after the first model download)
  3. drops duplicates (identical audio, or near-identical text - also against earlier batches)
  4. names the kept clips urdu_<n>.wav in sequence, continuing after the last one in the CSV
  5. copies them to output/audios/ and appends  audio,text,roman_urdu  rows to output/dataset.csv
  6. moves the processed originals to audios_done/

Transcripts are cached (transcripts_cache.json), so if the run is stopped just start it again.
Close output/dataset.csv in Excel before running - Excel locks the file.
"""
import argparse, csv, difflib, hashlib, json, os, re, shutil, sys, wave
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Urdu text in the console on Windows
except Exception:
    pass

HERE = Path(__file__).resolve().parent
IN_DIR = HERE / "audios"
DONE_DIR = HERE / "audios_done"
OUT_DIR = HERE / "output"
CSV_PATH = OUT_DIR / "dataset.csv"
CACHE = HERE / "transcripts_cache.json"
EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".mp4", ".webm"}
FIELDS = ["audio", "text", "roman_urdu"]


def natural_key(p):
    # "clip 2" before "clip 10"; originals before "(1)" copies
    return ("(" in p.name, [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)])


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def norm(t):
    return re.sub(r"[^\w]", "", t)


def similar(a, b, limit):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio() > limit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, help="number for the first new clip (default: continue after the CSV's last clip, or 1)")
    ap.add_argument("--min-sec", type=float, default=45, help="drop clips shorter than this (default 45)")
    ap.add_argument("--sim", type=float, default=0.90, help="text similarity above which a clip counts as a duplicate (default 0.90)")
    ap.add_argument("--model", default="large-v3-turbo", help="model name (downloaded on first run) or path to a local model folder")
    ap.add_argument("--beam", type=int, default=1, help="beam size: 1 = fast, 5 = slightly more accurate but slower")
    args = ap.parse_args()

    IN_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "audios").mkdir(parents=True, exist_ok=True)
    files = sorted((p for p in IN_DIR.iterdir() if p.suffix.lower() in EXTS), key=natural_key)
    if not files:
        sys.exit("No audio files found in the 'audios' folder.")

    # ---- existing dataset (earlier batches) ----
    old_rows = []
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as fh:
            old_rows = list(csv.DictReader(fh))
    old_hashes = {md5(p): p.name for p in (OUT_DIR / "audios").glob("*") if p.is_file()}
    nums = [int(m.group(1)) for r in old_rows if (m := re.match(r"urdu_(\d+)", r["audio"]))]
    start = args.start if args.start else (max(nums) + 1 if nums else 1)

    # ---- 1. cheap checks first: too short / identical audio ----
    from faster_whisper.audio import decode_audio

    dropped, cands, seen = [], [], {}
    for p in files:
        audio = decode_audio(str(p), sampling_rate=16000)
        dur = len(audio) / 16000
        if dur < args.min_sec:
            dropped.append((p.name, f"too short ({dur:.1f}s)")); continue
        h = md5(p)
        if h in old_hashes:
            dropped.append((p.name, f"identical audio to existing {old_hashes[h]}")); continue
        if h in seen:
            dropped.append((p.name, f"identical audio to {seen[h]}")); continue
        seen[h] = p.name
        cands.append((p, audio, h))
    print(f"{len(files)} files: {len(cands)} to transcribe, {len(dropped)} dropped already")

    # ---- 2. transcribe in Urdu (cached by file content) ----
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if any(h not in cache for _, _, h in cands):
        import ctranslate2
        from faster_whisper import WhisperModel

        try:
            gpu = ctranslate2.get_cuda_device_count() > 0
        except Exception:
            gpu = False
        print(f"Loading model '{args.model}' on {'GPU' if gpu else 'CPU'} (first run downloads it)...")
        model = WhisperModel(args.model, device="cuda" if gpu else "cpu",
                             compute_type="float16" if gpu else "int8")
        for i, (p, audio, h) in enumerate(cands, 1):
            if h not in cache:
                segs, _ = model.transcribe(audio, language="ur", vad_filter=True,
                                           condition_on_previous_text=False, beam_size=args.beam)
                cache[h] = " ".join(s.text.strip() for s in segs if s.text.strip())
                CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{i}/{len(cands)}  {p.name}  {cache[h][:40]}", flush=True)

    # ---- 3. drop empty / duplicate text ----
    prior = [(r["audio"], r["text"]) for r in old_rows]
    kept = []
    for p, _, h in cands:
        t = cache[h]
        if not t:
            dropped.append((p.name, "no speech")); continue
        dup = next((n for n, ot in prior + [(k[0].name, k[1]) for k in kept] if similar(t, ot, args.sim)), None)
        if dup:
            dropped.append((p.name, f"duplicate text of {dup}")); continue
        kept.append((p, t))

    # ---- 4. write: copy+rename clips, append CSV rows ----
    new_file = not CSV_PATH.exists()
    try:
        fh = open(CSV_PATH, "a", newline="", encoding="utf-8-sig" if new_file else "utf-8")
    except PermissionError:
        sys.exit(f"\nCannot write {CSV_PATH}. Close it in Excel and run again - nothing is lost, "
                 "transcripts are cached so it will finish in seconds.")
    with fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(FIELDS)
        for n, (p, t) in enumerate(kept, start):
            name = f"urdu_{n}{p.suffix.lower()}"
            shutil.copy(p, OUT_DIR / "audios" / name)
            w.writerow([name, t, ""])  # roman_urdu left empty
    # ---- 5. move processed originals out of the input folder ----
    DONE_DIR.mkdir(exist_ok=True)
    for p in files:
        shutil.move(str(p), DONE_DIR / p.name)

    log = "\n".join(f"{a}\t{b}" for a, b in dropped)
    (HERE / "dropped_log.txt").write_text(log, encoding="utf-8")
    span = f" (urdu_{start} .. urdu_{start + len(kept) - 1})" if kept else ""
    print(f"\nKept {len(kept)}{span}, dropped {len(dropped)} | dataset now has {len(old_rows) + len(kept)} rows")
    for a, b in dropped:
        print("  dropped:", a, "->", b)
    print(f"CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()
