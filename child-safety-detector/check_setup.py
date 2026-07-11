"""
check_setup.py
--------------
Run this FIRST if the app won't start:

    python check_setup.py

It checks every common failure point (Python version, missing
packages, missing Tesseract, port already in use) and tells you
exactly what to fix, in plain English -- instead of a scary traceback.
"""

import importlib
import socket
import sys

CHECK = "  [OK] "
FAIL = "  [FAIL] "

problems = []


def check_python_version():
    print("1. Python version...")
    major, minor = sys.version_info[0], sys.version_info[1]
    if major == 3 and minor >= 8:
        print(f"{CHECK}Python {major}.{minor} detected.")
    else:
        print(f"{FAIL}Python {major}.{minor} detected -- you need Python 3.8 or newer.")
        problems.append("Install Python 3.8+ from https://www.python.org/downloads/")


def check_packages():
    print("\n2. Required Python packages...")
    required = {
        "flask": "Flask",
        "pytesseract": "pytesseract",
        "PIL": "Pillow",
        "dotenv": "python-dotenv",
        "requests": "requests",
    }
    missing = []
    for import_name, pip_name in required.items():
        try:
            importlib.import_module(import_name)
            print(f"{CHECK}{pip_name} is installed.")
        except ImportError:
            print(f"{FAIL}{pip_name} is NOT installed.")
            missing.append(pip_name)

    if missing:
        problems.append(
            "Install missing packages with:\n"
            "     pip install -r requirements.txt\n"
            "   (If that fails, try: pip install --upgrade pip   then retry)"
        )

    # OpenCV/numpy are OPTIONAL -- screen_capture.py falls back to a
    # Pillow-only version automatically if these aren't installed.
    try:
        import cv2  # noqa: F401
        print(f"{CHECK}opencv-python-headless is installed (optional OCR boost active).")
    except ImportError:
        print(f"  [INFO] opencv-python-headless not installed -- this is OPTIONAL. "
              f"The app will use a Pillow-only fallback instead, which works fine.")


def check_tesseract():
    print("\n3. Tesseract OCR program (separate from the Python package)...")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"{CHECK}Tesseract {version} found.")
    except ImportError:
        print(f"{FAIL}Can't check -- pytesseract package isn't installed yet (see step 2).")
    except Exception:
        print(f"{FAIL}Tesseract program not found on your PATH.")
        problems.append(
            "Install Tesseract OCR (this is NOT a pip package, it's a separate program):\n"
            "     Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "     macOS:   brew install tesseract\n"
            "     Linux:   sudo apt-get install tesseract-ocr"
        )


def check_port():
    print("\n4. Port 5000 availability...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", 5000))
    sock.close()
    if result == 0:
        print(f"{FAIL}Something is already using port 5000.")
        problems.append(
            "Port 5000 is already in use. Either close whatever is using it, "
            "or change the port at the bottom of app.py, e.g. app.run(port=5050)."
        )
    else:
        print(f"{CHECK}Port 5000 is free.")


def check_screenshot():
    print("\n5. Screenshot capability...")
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        print(f"{CHECK}Screenshot captured successfully ({img.size[0]}x{img.size[1]}).")
    except ImportError:
        print(f"{FAIL}Can't check -- Pillow isn't installed yet (see step 2).")
    except Exception as e:
        print(f"{FAIL}Screenshot failed: {e}")
        problems.append(
            "Screenshot capture failed. On Linux, install the 'scrot' helper:\n"
            "     sudo apt-get install scrot\n"
            "   On Windows/macOS this should normally work out of the box -- "
            "make sure you're running this in a real desktop session, not a "
            "remote terminal with no display."
        )


if __name__ == "__main__":
    print("=" * 60)
    print(" Guardian Lens - Setup Diagnostic")
    print("=" * 60)

    check_python_version()
    check_packages()
    check_tesseract()
    check_port()
    check_screenshot()

    print("\n" + "=" * 60)
    if problems:
        print(f" Found {len(problems)} issue(s) to fix:\n")
        for i, p in enumerate(problems, 1):
            print(f" {i}. {p}\n")
    else:
        print(" Everything looks good! Run: python app.py")
    print("=" * 60)
