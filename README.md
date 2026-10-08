# Urdu Dataset Formation Tool

Turn long Urdu recordings into a clean **speech dataset**: short audio clips paired with Urdu transcripts, saved as a CSV (and optionally an Excel file).

Made for students who want to build an Urdu speech-to-text (ASR) dataset without writing any code. You copy audio in, run one command, and get a numbered dataset out.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/syedakinzabatool/urdu-dataset-formation-tool/blob/main/trim_remove_bg_music.ipynb)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Table of contents
- [How it works](#how-it-works)
- [What you need](#what-you-need)
- [Step-by-step guide](#step-by-step-guide)
  - [Step 0 - Get the project](#step-0---get-the-project)
  - [Step 1 - One-time setup](#step-1---one-time-setup)
  - [Step 2 - Prepare clips from long recordings (Colab)](#step-2---prepare-clips-from-long-recordings-colab)
  - [Step 3 - Transcribe the clips](#step-3---transcribe-the-clips)
  - [Step 4 - Make an Excel file (optional)](#step-4---make-an-excel-file-optional)
  - [Step 5 - Check and correct the transcripts](#step-5---check-and-correct-the-transcripts)
- [What you get](#what-you-get)
- [Rules applied automatically](#rules-applied-automatically)
- [Command options](#command-options)
- [Adding more batches](#adding-more-batches)
- [Troubleshooting](#troubleshooting)
- [Using audio responsibly](#using-audio-responsibly)
- [Project layout](#project-layout)
- [Credits](#credits)
- [Contributing](#contributing)
- [License](#license)

---

## How it works

```
 long recording(s)                        short clips
 (talk + background music)   Step 2       (46 s, voice only)     Step 3
 ───────────────────────►  Colab notebook ───────────────────►  transcribe_audios.py
                           removes music,                        · drops short / duplicate / silent clips
                           cuts 46 s clips                       · writes Urdu text for each clip
                                                                 · renames clips urdu_1, urdu_2, ...
                                                                          │
                                                                          ▼
                                                 output/dataset.csv  +  output/audios/urdu_<n>.wav
                                                                          │  Step 4 (optional)
                                                                          ▼
                                                                 output/dataset.xlsx
```

- **Step 2 is only needed** if your recordings are long and/or have background music. If you already have clean clips of 45 seconds or more, skip straight to Step 3.
- **Step 3 runs on your own computer.** After the one-time model download, it works offline.

## What you need

| Need | Why |
|---|---|
| A computer with **Windows, macOS or Linux** | Tested on Windows 11 with Python 3.11; macOS and Linux should work the same way but are untested |
| **Python 3.10 or newer** ([python.org](https://www.python.org/downloads/)) | Runs the scripts. On Windows, tick **"Add Python to PATH"** during install |
| **Internet, once** | Downloads the speech model (about 1.6 GB) the first time you transcribe |
| About **3 GB free disk space** | Model + your clips |
| A **Google account** (only for Step 2) | The Colab notebook uses a free Google GPU |
| [VS Code](https://code.visualstudio.com/) (recommended) | Easy way to open the folder and use the terminal |

You do **not** need to install ffmpeg or have a GPU for Step 3. A GPU (NVIDIA) just makes it much faster.

---

## Step-by-step guide

### Step 0 - Get the project

Either use git:

```bash
git clone https://github.com/syedakinzabatool/urdu-dataset-formation-tool.git
cd urdu-dataset-formation-tool
```

or click **Code → Download ZIP** on GitHub and extract it.

Then open the folder in VS Code (**File → Open Folder...**) and open a terminal (**Terminal → New Terminal**). All commands below are typed in that terminal.

### Step 1 - One-time setup

Create a private Python environment for the project and install the two libraries it needs.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

When the environment is active you will see `(.venv)` at the start of the terminal line. **Every time you open a new terminal, activate it again** (the `Activate` / `source` line above).

> If PowerShell says *"running scripts is disabled"*, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and try the activate line again.
> If `python` is not recognised on Windows, try `py` instead.

### Step 2 - Prepare clips from long recordings (Colab)

Skip this step if you already have clean clips of 45 seconds or more.

1. Click the **Open In Colab** badge at the top of this page (or upload `trim_remove_bg_music.ipynb` to [colab.research.google.com](https://colab.research.google.com)).
2. Choose **Runtime → Change runtime type → T4 GPU**.
3. Run **cell 1** (installs the tools) and wait until it finishes.
4. Run **cell 2**, then click **Choose files** and select your **original** recording(s).
   - The notebook removes the background music, finds where the speaker starts talking, and cuts the rest into back-to-back **46-second** clips (mono WAV, 44.1 kHz).
   - A leftover piece shorter than 46 s at the end is dropped.
   - When it finishes, your browser downloads **`clips.zip`**. As a rough size guide, a 17-minute recording became 23 clips and about 85 MB.
5. Unzip `clips.zip` and copy the `.wav` files into this project's **`audios`** folder.
6. Optional: run **cell 3** to clean the Colab workspace before uploading another recording.

> **Why 46 seconds?** The transcription step drops clips shorter than 45 s, so 46 s clips always pass.
>
> **Several recordings, several sessions?** Each Colab session numbers clips from `urdu_001` again. Before running cell 2 for a new recording, change `START_INDEX` at the top of the cell (for example to `101`). Otherwise two different clips can share a file name, and the backup of the older one in `audios_done/` gets overwritten.

### Step 3 - Transcribe the clips

1. Make sure your clips are in the **`audios`** folder (`.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.opus`, `.aac`, `.mp4`, `.webm`).
2. If `output/dataset.csv` or `output/dataset.xlsx` exist, **close them in Excel**. Excel locks the file and the last step cannot save.
3. Run:

   ```bash
   python transcribe_audios.py
   ```

4. Wait. The first run downloads the speech model (about 1.6 GB, once). Then each clip is transcribed. As a rough guide, a normal laptop CPU needs about 2 minutes per clip; a PC with an NVIDIA GPU is much faster.
   - Keep the laptop **plugged in and awake** during a long run.
   - You can stop with **Ctrl+C** and run the same command again: finished clips are remembered and are not redone.

You will see progress like this (numbers are just an example):

```
23 files: 21 to transcribe, 2 dropped already
Loading model 'large-v3-turbo' on CPU (first run downloads it)...
1/21  urdu_001.wav  ...
...
Kept 20 (urdu_1 .. urdu_20), dropped 3 | dataset now has 20 rows
  dropped: urdu_007.wav -> duplicate text of urdu_003.wav
CSV: ...\output\dataset.csv
```

To pick the first clip number yourself (for example your batch should be 441-470):

```bash
python transcribe_audios.py --start 441
```

### Step 4 - Make an Excel file (optional)

A CSV cannot store text wrapping or right-to-left alignment. To get a nicely formatted spreadsheet:

```bash
python make_excel.py
```

This creates `output/dataset.xlsx` from `output/dataset.csv` (close the `.xlsx` in Excel first). It is rebuilt from the CSV every time, so **make your corrections in the CSV, not in the `.xlsx`**: changes made only in the `.xlsx` are overwritten the next time you run the script.

### Step 5 - Check and correct the transcripts

**The text is written by a machine and will contain mistakes**, especially for names, rare words and noisy audio. A dataset is only as good as its text, so:

1. Open `output/dataset.csv` (VS Code or Excel).
2. Listen to each clip in `output/audios/` and fix wrong words in the **`text`** column.
3. If you save from Excel, choose **Save As → CSV UTF-8**. Plain "CSV" can turn Urdu letters into `?`.
4. Do **not** change the `audio` names by hand. The next batch continues numbering from the highest `urdu_<n>` it finds there.

The **`roman_urdu`** column is left empty on purpose: this tool does not write Roman Urdu. Fill it by hand or with another tool if you need it.

---

## What you get

| Path | What it is |
|---|---|
| `output/dataset.csv` | The dataset. Columns: `audio`, `text`, `roman_urdu`. Each batch is **added at the end**. |
| `output/audios/` | The kept clips, renamed `urdu_1.wav`, `urdu_2.wav`, ... to match the CSV |
| `output/dataset.xlsx` | Same table with wrapped, right-to-left text (from `make_excel.py`) |
| `audios_done/` | Your original files, moved here after processing. `audios/` is empty again for the next batch. |
| `dropped_log.txt` | Which clips were dropped in the **latest** batch, and why |
| `transcripts_cache.json` | Saved transcripts so an interrupted run can continue. Safe to ignore. |

Example rows (illustrative):

| audio | text | roman_urdu |
|---|---|---|
| urdu_1.wav | آج موسم بہت اچھا ہے | |
| urdu_2.wav | ہم کل لاہور جا رہے ہیں | |

## Rules applied automatically

- Clips **shorter than 45 s** are dropped (`--min-sec`).
- **Duplicates** are dropped: identical audio, or text more than 90% similar to an earlier clip (`--sim`). This is checked within the batch and against all earlier batches. The original is kept; the copy (for example `name (1).wav`) is dropped.
- Clips with **no speech** (music or silence) are dropped.
- Kept clips are **numbered in sequence**, continuing after the last clip in the CSV (or from `--start`).

## Command options

```bash
python transcribe_audios.py [options]
```

| Option | Default | Meaning |
|---|---|---|
| `--start N` | after last clip in the CSV, else 1 | Number of the first new clip |
| `--min-sec S` | `45` | Drop clips shorter than `S` seconds |
| `--sim X` | `0.90` | Text similarity (0-1) above which a clip counts as a duplicate |
| `--beam N` | `1` | `1` = fast. `5` = slightly more accurate but slower |
| `--model NAME` | `large-v3-turbo` | Model name (downloaded on first use) or path to a local model folder. `tiny` is fast but much less accurate, so use it only to test your setup. |

Run `python transcribe_audios.py --help` to see them in your terminal.

## Adding more batches

Just repeat Step 2 → Step 3 with new recordings. The tool:

- keeps adding rows to the same `output/dataset.csv`,
- continues numbering where the last batch stopped,
- checks new clips against all earlier ones, so a clip you already processed is dropped as a duplicate.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Reinstall Python and tick **Add Python to PATH**, or try `py` instead of `python` (Windows) |
| `ModuleNotFoundError: No module named 'faster_whisper'` | The environment is not active or Step 1 was skipped. Activate `.venv` and run `pip install -r requirements.txt` |
| PowerShell: *running scripts is disabled* | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again |
| `No audio files found in the 'audios' folder.` | Put the clips directly inside `audios/` (not in a sub-folder) and check the file type is supported |
| `Cannot write ...dataset.csv` | Close the file in Excel and run the **same command** again. Nothing is lost; transcripts are cached and it finishes in seconds |
| Every clip is dropped as "too short" | Your clips are under 45 s. Cut longer clips (Step 2) or lower the limit, for example `--min-sec 30` |
| It is very slow | Normal on a CPU. Keep `--beam 1` (default), keep the laptop awake, or use a PC with an NVIDIA GPU |
| Model download fails or stops | Check your internet and run the command again. The model is stored once in `~/.cache/huggingface` |
| Urdu shows as `?` or boxes in Excel | Save with **CSV UTF-8**, or use `dataset.xlsx` (Step 4) |
| Colab: upload button does not appear | Re-run cell 2 |
| Colab: *"No speech found, skipping this file"* | The recording has no detectable speech. Check the file |
| Colab: GPU not available | Free GPUs are limited. Wait and try again later, or run on CPU (much slower) |

---

## Using audio responsibly

This repository contains **no audio and no data**. You are responsible for what you put in it.

- Only use recordings you **own, have permission to use, or that carry a licence allowing it**. Check the terms before using audio from YouTube, TV, radio or podcasts, and before publishing a dataset made from them.
- If the voices belong to real people, respect their **consent and privacy**.
- Your clips, transcripts and `output/` folder are listed in `.gitignore` so they are not uploaded to GitHub by accident. Share a finished dataset deliberately, for example through Hugging Face or Google Drive, and only if you have the right to.

## Project layout

```
urdu-dataset-formation-tool/
├── README.md                    this guide
├── LICENSE                      MIT licence
├── requirements.txt             Python libraries (faster-whisper, openpyxl)
├── trim_remove_bg_music.ipynb   Step 2: Colab notebook (remove music, cut 46 s clips)
├── transcribe_audios.py         Step 3: transcribe, de-duplicate, rename, write CSV
├── make_excel.py                Step 4: CSV -> formatted Excel
└── audios/                      INPUT: put your clips here
```

Created when you run the tool (and ignored by git): `output/`, `audios_done/`, `transcripts_cache.json`, `dropped_log.txt`.

## Credits

This project is a thin workflow around these excellent open-source tools:

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and OpenAI's [Whisper](https://github.com/openai/whisper) (`large-v3-turbo`) for speech recognition
- [Demucs](https://github.com/facebookresearch/demucs) (`htdemucs`) for removing background music
- [Silero VAD](https://github.com/snakers4/silero-vad) for finding where speech starts
- [openpyxl](https://openpyxl.readthedocs.io/) for the Excel file

Each has its own licence; please check them if you redistribute anything built with them.

## Contributing

Found a bug or have an idea? Please open an [issue](https://github.com/syedakinzabatool/urdu-dataset-formation-tool/issues). Pull requests are welcome; for bigger changes, open an issue first so we can talk it through.

## License

[MIT](LICENSE) © 2026 Syeda Kinza Batool
