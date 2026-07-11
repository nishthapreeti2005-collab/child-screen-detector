"""
screen_capture.py
------------------
Takes a screenshot of the computer screen and hands it back as an
in-memory image (a PIL Image object). We deliberately do NOT save
the screenshot to disk anywhere -- it is used once, for OCR, and
then discarded. This matches the "privacy protection" requirement:
we only ever store the extracted TEXT, never the picture itself.

For the hackathon demo, this captures whatever is on the screen of
the laptop running this app. In a real product this would run as a
small background agent on the child's device.
"""

from PIL import ImageGrab, ImageOps

# OpenCV is used for a small image-preprocessing boost (grayscale +
# thresholding), but it's a large download (60-90MB) and not strictly
# required -- if it isn't installed (e.g. it failed to download on a
# slow/restricted network), we fall back to an equivalent pure-Pillow
# version below so the app still works fully without it.
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def capture_screenshot():
    """
    Grab the current screen and return it as a PIL Image.
    Works out of the box on Windows and macOS.
    On Linux you may need to install 'scrot' first:
        sudo apt-get install scrot
    """
    try:
        screenshot = ImageGrab.grab()
        return screenshot
    except Exception as e:
        raise RuntimeError(
            "Could not capture the screen. On Linux, run: sudo apt-get install scrot. "
            f"Original error: {e}"
        )


def preprocess_for_ocr(pil_image):
    """
    Clean up the image a bit before OCR, which makes Tesseract noticeably
    more accurate on screenshots (small UI text, chat bubbles, etc):
      1. Convert to grayscale
      2. Increase contrast with thresholding

    Uses OpenCV if it's installed (slightly faster), otherwise falls
    back to an equivalent Pillow-only version that needs no extra
    dependencies at all.
    """
    if OPENCV_AVAILABLE:
        img = np.array(pil_image)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        return thresh  # NumPy array -- Tesseract can read this directly

    # ---- Pillow-only fallback (no OpenCV/NumPy needed) ----
    gray = ImageOps.grayscale(pil_image)
    # Simple black/white threshold, same effect as cv2.threshold above
    thresh = gray.point(lambda p: 255 if p > 150 else 0)
    return thresh  # PIL Image -- Tesseract can read this directly too
