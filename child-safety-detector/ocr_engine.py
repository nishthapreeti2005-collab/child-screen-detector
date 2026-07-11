"""
ocr_engine.py
-------------
Small wrapper around Tesseract OCR (via pytesseract) that turns a
screenshot into plain text so we can analyze it for safety risks.

IMPORTANT (beginner note):
"pytesseract" is just a Python bridge -- you ALSO need the real
Tesseract OCR program installed on your computer for this to work.
See README.md for the one-line install command for your OS.
"""

import pytesseract


def extract_text(image):
    """
    Run OCR on an image (PIL Image or NumPy array from OpenCV) and
    return the extracted text as a clean string.
    """
    try:
        raw_text = pytesseract.image_to_string(image)
        # Collapse extra blank lines/whitespace so stored text is tidy
        cleaned = " ".join(raw_text.split())
        return cleaned
    except pytesseract.TesseractNotFoundError:
        # Friendly error so the demo doesn't just crash with a stack trace
        return "[OCR ERROR] Tesseract is not installed. See README.md setup steps."
