"""
app.py
------
The Flask backend that ties everything together:
  screen_capture -> ocr_engine -> ai_analyzer -> database -> dashboard

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import threading
import time

from flask import Flask, jsonify, render_template, request

import database
import screen_capture
import ocr_engine
import ai_analyzer
import chatbot

app = Flask(__name__)

# ---- simple global state for the background monitoring loop ----
monitoring_active = False
monitor_thread = None
SCAN_INTERVAL_SECONDS = 15  # how often we scan the screen while monitoring


def run_one_scan():
    """
    Capture the screen once, OCR it, analyze it, and store the result.
    Returns the result dict so callers (routes or the background loop)
    can reuse it.
    """
    screenshot = screen_capture.capture_screenshot()
    processed = screen_capture.preprocess_for_ocr(screenshot)
    text = ocr_engine.extract_text(processed)

    result = ai_analyzer.analyze_text(text)

    database.save_scan(
        extracted_text=text,
        category=result["category"],
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        reason=result["reason"],
        suggestion=result["suggestion"],
    )
    return result


def monitoring_loop():
    """Runs in a background thread while monitoring is ON."""
    global monitoring_active
    while monitoring_active:
        try:
            run_one_scan()
        except Exception as e:
            # Never let a single bad scan kill the background thread
            print(f"[monitoring_loop] scan failed: {e}")
        time.sleep(SCAN_INTERVAL_SECONDS)


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@app.route("/")
def dashboard():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """Tell the frontend whether monitoring is currently on."""
    return jsonify({"monitoring_active": monitoring_active})


@app.route("/api/start_monitoring", methods=["POST"])
def start_monitoring():
    """Turn ON background monitoring (requires explicit user action)."""
    global monitoring_active, monitor_thread
    if not monitoring_active:
        monitoring_active = True
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
    return jsonify({"monitoring_active": monitoring_active})


@app.route("/api/stop_monitoring", methods=["POST"])
def stop_monitoring():
    """Turn OFF background monitoring."""
    global monitoring_active
    monitoring_active = False
    return jsonify({"monitoring_active": monitoring_active})


@app.route("/api/scan_once", methods=["POST"])
def scan_once():
    """Manual 'Scan Now' button -- runs a single scan on demand."""
    try:
        result = run_one_scan()
        return jsonify({"success": True, "result": result})
    except Exception as e:
        # Print the full error to THIS terminal window too, not just to
        # the browser -- makes debugging much easier since it's visible
        # right here without needing to find/read a popup in the browser.
        import traceback
        print("\n" + "=" * 60)
        print("[scan_once] Scan failed with this error:")
        traceback.print_exc()
        print("=" * 60 + "\n")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/scans")
def api_scans():
    """Return recent scans + summary stats for the dashboard."""
    return jsonify({
        "scans": database.get_recent_scans(limit=25),
        "stats": database.get_stats(),
    })


@app.route("/api/clear_data", methods=["POST"])
def clear_data():
    """Privacy control: let the parent wipe all stored scan history."""
    database.clear_all_scans()
    return jsonify({"success": True})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """AI Safety Assistant chatbot endpoint."""
    question = request.json.get("question", "")
    if not question.strip():
        return jsonify({"answer": "Please type a question first."})
    answer = chatbot.get_answer(question)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    database.init_db()
    print("=" * 60)
    print(" AI Child Screen Safety Detector")
    print(" Open http://127.0.0.1:5000 in your browser")
    print("=" * 60)
    try:
        # use_reloader=False avoids Flask starting a second background
        # process, which can otherwise duplicate the monitoring thread.
        app.run(debug=True, port=5000, use_reloader=False)
    except OSError as e:
        print("\n[ERROR] Could not start the server.")
        print(f"        {e}")
        print("        This usually means port 5000 is already in use.")
        print("        Close whatever is using it, or edit the port number")
        print("        at the bottom of app.py (e.g. app.run(port=5050)).")
