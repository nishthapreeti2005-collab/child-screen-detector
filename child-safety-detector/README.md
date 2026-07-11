# 🛡️ Guardian Lens — AI Child Screen Safety Detector

An AI-powered tool that helps parents spot harmful content and risky
online behavior on their child's screen — cyberbullying, adult content,
hate/violent language, scams, and grooming-style messages — and alerts
them in a simple dashboard.

Built for a hackathon: **simple, beginner-friendly code**, no cloud
infrastructure, runs entirely on one laptop.

---

## 1. Project Folder Structure

```
child-safety-detector/
│
├── app.py                # Flask backend + all routes
├── database.py            # SQLite setup + save/read scan results
├── screen_capture.py       # Takes a screenshot (in-memory, never saved)
├── ocr_engine.py           # Tesseract OCR: image -> text
├── ai_analyzer.py          # Classifies text: category / risk / suggestion
├── chatbot.py              # "AI Safety Assistant" Q&A logic
├── requirements.txt         # Package list
├── start.bat                # Windows one-click setup + launch
├── check_setup.py           # Standalone diagnostic tool (run if setup issues occur)
├── .env.example            # Copy to .env to add an optional AI API key
├── templates/
│   └── index.html          # Dashboard page
└── static/
    ├── style.css            # Dashboard styling
    └── script.js            # Dashboard interactivity (fetch calls)
```

A `safety_data.db` SQLite file will be created automatically the first
time you run the app — that's your local, private database.

---

## 2. Required Installations

### Step A — Python packages
```bash
cd child-safety-detector
python -m venv venv          # optional but recommended
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step B — Tesseract OCR (the actual OCR program, not just the Python wrapper)

- **Windows:** Download and install from
  https://github.com/UB-Mannheim/tesseract/wiki, then make sure the
  install folder (e.g. `C:\Program Files\Tesseract-OCR`) is on your PATH.
- **macOS:** `brew install tesseract`
- **Linux (Debian/Ubuntu):** `sudo apt-get install tesseract-ocr`

### Step C — Screenshot support on Linux only
`ImageGrab` needs a screenshot helper on Linux:
```bash
sudo apt-get install scrot
```
(Not needed on Windows or macOS.)

---

## 3. Complete Code

All files are included in this folder — see the structure above. Every
file has beginner-friendly comments explaining what each part does.

**Nothing is skipped** — `app.py`, `database.py`, `screen_capture.py`,
`ocr_engine.py`, `ai_analyzer.py`, `chatbot.py`, `index.html`,
`style.css`, and `script.js` are all complete and ready to run.

---

## 4. Optional: Enable a real AI model (Gemini/OpenAI)

The app works immediately with **zero API keys** — it uses a fast,
offline, keyword-based safety classifier by default (great for a
reliable hackathon demo with no WiFi risk).

To use a real LLM for smarter, more nuanced classification instead:

1. Copy `.env.example` to `.env`
2. Get a **free** Gemini key: https://aistudio.google.com/apikey
3. Fill in:
   ```
   GEMINI_API_KEY=your_key_here
   AI_PROVIDER=gemini
   ```
4. Restart the app.

If the API call ever fails (no internet, quota, etc.) the app
automatically falls back to the offline detector — it will never crash
your demo.

---

## 5. How to Run Locally

### Option A — Windows one-click launcher
Just double-click **`start.bat`**. It will automatically:
1. Create a virtual environment (first run only) and rebuild it if it's broken
2. Install/update all required packages
3. Verify Flask actually imports correctly
4. Run a diagnostic check
5. Open your browser and start the Flask server

Everything (setup + the running server) happens **in that same window** —
it deliberately does not open a second console window, since some
locked-down/lab computers silently block spawned windows. Watch that
window for a red `[ERROR]` line if something goes wrong, and press
CTRL+C in it to stop the server.

### Option B — Manual (Windows/macOS/Linux)
```bash
python app.py
```

Then open your browser at:
```
http://127.0.0.1:5000
```

### Using the app
1. Click **"Start Safety Monitoring"** to begin scanning the screen
   every 15 seconds, or click **"Scan Now"** for a single instant scan.
2. Watch the **Safety Score ring** and **Recent Detections** list
   update live, with a real-time category breakdown chart.
3. Use the **filter tabs** (All / Safe / Warning / High Risk) or click a
   summary card to instantly filter the detection list.
4. Click any detection to **expand it** and see the extracted text.
5. Toggle **🌙/☀️ dark mode** top-right.
6. Click the **💬 chat bubble** bottom-right to ask the AI Safety
   Assistant a parenting question (quick-reply chips included).
7. Click **"Clear Data"** anytime to permanently wipe stored history
   (privacy control).

> **Demo tip:** Open Notepad/TextEdit, type a test phrase like
> `"You are useless, nobody likes you"`, keep it on screen, then click
> **Scan Now** — you'll immediately see a High-risk Cyberbullying alert
> pop up as a toast notification and appear on the dashboard. Try a
> profanity phrase too (e.g. "what the fuck") to see the dedicated
> Profanity / Inappropriate Language category in action.

---

## 6. Privacy Design

- Screenshots are processed **entirely in memory** and are **never**
  written to disk.
- Only a short text snippet (max 500 characters) plus the AI's
  classification is stored, and only in a **local SQLite file** on
  your own machine — nothing is sent to any server except the optional,
  user-provided AI API call.
- Monitoring only runs when explicitly turned **ON** by the parent, and
  can be turned **OFF** at any time.
- A **"Clear Data"** button lets the parent wipe all history instantly.

---

## Troubleshooting — "The app isn't running"

**First, always run this:**
```bash
python check_setup.py
```
It checks your Python version, all required packages, Tesseract, port 5000, and
screenshot capability, and tells you exactly what's wrong in plain English.

Common issues:

| Symptom | Cause | Fix |
|---|---|---|
| `pip install` fails / "no matching distribution" | Pinned package versions don't have a wheel for your Python version | Already fixed — `requirements.txt` now uses flexible version ranges. Re-run `pip install -r requirements.txt` |
| `'python' is not recognized...` (Windows) | Python not on PATH, or only `py` is available | Use `start.bat` (it auto-detects `python` or `py`), or reinstall Python and check "Add to PATH" |
| `TesseractNotFoundError` | Tesseract OCR program isn't installed (it's separate from the `pytesseract` pip package) | Install it — see step 2B above — then restart the app |
| Screenshot / `ImageGrab` error on Linux | Missing screenshot helper | `sudo apt-get install scrot` |
| `OSError: [Errno 98] Address already in use` | Something else is using port 5000 | Close it, or change `app.run(port=5000)` to another port in `app.py` |
| Page loads but "Scan Now" shows an alert popup | Backend caught an error (e.g. screenshot/OCR failed) | Read the popup text — it tells you the exact cause. Also check the terminal running `app.py` for the full error |
| Blank dashboard, nothing loads | `app.py` isn't running, or crashed | Look at the terminal/window running `app.py` for a red `[ERROR]` message |
| `ModuleNotFoundError: No module named 'flask'` | Packages installed outside the virtual environment, or venv not activated | Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux), then `pip install -r requirements.txt` again |
| Double-clicking `start.bat` does nothing, or nothing visible happens | Older versions spawned a separate console window, which some locked-down/lab PCs silently block | Fixed — the latest `start.bat` runs everything in a single window, so there's no second window that can fail to open. If it *still* seems to do nothing, right-click `start.bat` → "Run as administrator", or open Command Prompt in this folder and run `venv\Scripts\python.exe app.py` directly to see the exact error text |
| `pip install` is slow or seems stuck at Step 3 | Downloading packages (especially opencv-python-headless, ~30-60MB) over a slow connection | Just wait -- it can genuinely take a minute or two on slow WiFi. If it truly never finishes after several minutes, try a different network (e.g. phone hotspot) and re-run `start.bat` |

If none of these match what you're seeing, run `python check_setup.py`, copy
its full output, and share the exact error message/traceback — "not
working" alone can mean a dozen different things, so the precise error text
is what actually pinpoints the fix.

---

## Hackathon Problem Statement

Children increasingly face online risks — cyberbullying, exposure to
adult content, scams, and even grooming — often without their parents'
knowledge, because manually reviewing every app/message is impractical.
Existing parental-control tools mostly just **block** apps/sites; they
rarely **explain** *why* something is risky or **coach** the parent on
what to do next.

## Solution

Guardian Lens periodically captures the screen, extracts visible text
with OCR, and uses an AI classifier to flag risky content into clear
categories with a risk score and a plain-English explanation — plus a
built-in AI assistant that gives parents practical next steps. All
processing and storage stays local for privacy.

## System Architecture

```
 [Screen] --screenshot--> [OpenCV preprocess] --> [Tesseract OCR: text]
                                                        |
                                                        v
                                            [AI Analyzer: category,
                                             risk score, reason,
                                             suggestion]
                                                        |
                                                        v
                                          [SQLite: store text + result]
                                                        |
                                                        v
                                [Flask REST API] <--> [Dashboard (HTML/JS)]
                                                        |
                                                        v
                                        [AI Safety Assistant chatbot]
```

## Future Improvements

- Deploy as a lightweight background agent on the child's device (not
  just the demo laptop) with a companion mobile app for real-time
  parent push notifications.
- Add image-based detection (not just OCR text) using a vision model to
  catch harmful content in pictures/videos, not only text.
- Weekly/monthly trend reports and a "digital wellbeing" score over time.
- Multi-child, multi-device profiles with per-child settings.
- On-device (offline) small AI model instead of keyword rules, for
  better nuance without any cloud dependency.

## How to Present it to Judges

1. **Open with the problem** (10s): "Parents can't manually monitor
   every message their kid receives — Guardian Lens does it for them."
2. **Live demo** (60-90s): Open the dashboard, show the Safety Score
   ring at 100%. Type a bullying phrase in Notepad, click **Scan Now**,
   and watch the alert appear instantly with category, risk %, and a
   concrete suggestion.
3. **Show the chatbot** (15s): Ask "What should I do if my child
   receives bullying messages?" live.
4. **Highlight privacy** (15s): Point out screenshots are never saved,
   everything is local, and monitoring has an explicit ON/OFF switch.
5. **Close with impact + roadmap** (15s): Mention the architecture is
   simple today but designed to scale to a real on-device agent with
   push notifications and vision-based detection.
