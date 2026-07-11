"""
ai_analyzer.py
--------------
This is the "brain" of the app. It looks at text extracted from the
screen and decides:
   - category      (Safe / Cyberbullying / Adult Content / Hate-Violence /
                     Scam-Suspicious Link / Suspicious Message)
   - risk_level     (Safe / Medium / High)
  - risk_score      (0-100)
  - reason          (why it was flagged, in plain English)
  - suggestion      (what the parent should do)

DESIGN CHOICE (important for a reliable hackathon demo):
We use a fast, offline, KEYWORD-BASED detector as the default engine.
It needs no internet connection and no API key, so your demo never
breaks on stage because of WiFi or quota issues.

If the parent adds a free Gemini or OpenAI API key in ".env", we
instead send the text to that model for a smarter, more nuanced
judgement -- but if that call ever fails for any reason (no internet,
bad key, rate limit) we automatically fall back to the rule-based
engine so the app never crashes mid-demo.
"""

import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "none").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------
# 1. RULE-BASED ENGINE (always available, always fast)
# ---------------------------------------------------------------------

# Each category maps to keywords/phrases that hint at that risk type.
# This is intentionally simple and easy to extend for a hackathon demo.
CATEGORY_KEYWORDS = {
    "Cyberbullying": [
        "useless", "nobody likes you", "kill yourself", "ugly", "loser",
        "stupid", "hate you", "worthless", "no friends", "you suck",
        "get lost", "everyone hates you", "freak", "idiot",
    ],
    "Profanity / Inappropriate Language": [
        "fuck", "fucking", "fucked", "shit", "bullshit", "bitch",
        "asshole", "ass", "bastard", "damn", "goddamn", "crap", "piss",
        "dick", "douchebag", "motherfucker", "wtf", "stfu", "screw you",
    ],
    "Adult Content": [
        "nude", "porn", "sex video", "xxx", "onlyfans", "nsfw",
        "explicit content", "sexting", "send pics",
    ],
    "Hate/Violent Language": [
        "kill you", "i will hurt you", "beat you up", "bring a gun",
        "terrorist", "slur", "racist", "i'll kill", "stab", "shoot you",
    ],
    "Scam / Suspicious Link": [
        "click here", "you won", "free gift card", "verify your account",
        "urgent action required", "bit.ly", "claim your prize",
        "limited time offer", "act now", "password expired", "wire transfer",
    ],
    "Suspicious Message": [
        "don't tell your parents", "keep this secret", "meet me alone",
        "send your address", "what's your address", "are you home alone",
        "our little secret", "delete this conversation",
    ],
}

# How risky each category is by default (used for the score)
CATEGORY_BASE_SCORE = {
    "Cyberbullying": 80,
    "Profanity / Inappropriate Language": 55,
    "Adult Content": 90,
    "Hate/Violent Language": 90,
    "Scam / Suspicious Link": 65,
    "Suspicious Message": 85,
}

SUGGESTIONS = {
    "Cyberbullying": "Talk with your child calmly and review the conversation together. Consider reporting/blocking the sender.",
    "Profanity / Inappropriate Language": "Consider having a conversation about appropriate language. This alone isn't dangerous, but keep an eye on the context it's used in.",
    "Adult Content": "Restrict access to the app/site immediately and have an age-appropriate conversation about what they saw.",
    "Hate/Violent Language": "Take this seriously -- save evidence and consider reporting to the platform or school authorities.",
    "Scam / Suspicious Link": "Do not click any links. Teach your child to recognize scams and verify with a trusted adult first.",
    "Suspicious Message": "This pattern is common in online grooming. Talk to your child now and consider reporting the contact.",
    "Safe": "No action needed. Keep having open conversations about online safety.",
}


def _find_keyword_hits(text_lower, keywords):
    """
    Return the list of keywords/phrases that appear in text_lower as
    whole words (using \\b word boundaries), not just as a substring.
    This is important for short words like "ass" or "damn" -- without
    word boundaries, "ass" would wrongly match inside "class" or
    "assignment". re.escape() keeps special characters (like the
    apostrophe in "don't tell your parents") safe to search for.
    """
    hits = []
    for kw in keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text_lower):
            hits.append(kw)
    return hits


def _rule_based_analysis(text):
    """Scan the text for known risky keywords and score the worst match."""
    if not text or not text.strip():
        return {
            "category": "Safe",
            "risk_level": "Safe",
            "risk_score": 0,
            "reason": "No readable text was found on screen.",
            "suggestion": SUGGESTIONS["Safe"],
        }

    text_lower = text.lower()
    best_category = None
    best_score = 0
    matched_words = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = _find_keyword_hits(text_lower, keywords)
        if hits:
            score = CATEGORY_BASE_SCORE[category] + min(len(hits) - 1, 3) * 3
            if score > best_score:
                best_score = score
                best_category = category
                matched_words = hits

    # Also catch generic shortened/suspicious links with a quick regex
    if re.search(r"https?://\S+|www\.\S+", text_lower) and best_category is None:
        best_category = "Scam / Suspicious Link"
        best_score = 55
        matched_words = ["link detected"]

    if best_category is None:
        return {
            "category": "Safe",
            "risk_level": "Safe",
            "risk_score": 5,
            "reason": "No risky keywords or patterns were detected.",
            "suggestion": SUGGESTIONS["Safe"],
        }

    risk_score = min(best_score, 100)
    if risk_score >= 80:
        risk_level = "High"
    elif risk_score >= 50:
        risk_level = "Medium"
    else:
        risk_level = "Safe"

    return {
        "category": best_category,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "reason": f"Detected phrase(s): {', '.join(matched_words[:3])}",
        "suggestion": SUGGESTIONS.get(best_category, SUGGESTIONS["Safe"]),
    }


# ---------------------------------------------------------------------
# 2. OPTIONAL AI ENGINE (Gemini or OpenAI) -- used only if a key is set
# ---------------------------------------------------------------------

AI_PROMPT_TEMPLATE = """You are a child-safety content classifier.
Read the text below, which was captured from a child's screen.
Classify it and respond with ONLY valid JSON, no extra words, in this exact format:
{{
  "category": "Safe" | "Cyberbullying" | "Profanity / Inappropriate Language" | "Adult Content" | "Hate/Violent Language" | "Scam / Suspicious Link" | "Suspicious Message",
  "risk_level": "Safe" | "Medium" | "High",
  "risk_score": <integer 0-100>,
  "reason": "<one short sentence explaining why>",
  "suggestion": "<one short, practical sentence of advice for the parent>"
}}

Text from screen:
\"\"\"{text}\"\"\"
"""


def _call_gemini(text):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    prompt = AI_PROMPT_TEMPLATE.format(text=text[:1000])
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    raw_reply = data["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_ai_json(raw_reply)


def _call_openai(text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    prompt = AI_PROMPT_TEMPLATE.format(text=text[:1000])
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    raw_reply = data["choices"][0]["message"]["content"]
    return _parse_ai_json(raw_reply)


def _parse_ai_json(raw_reply):
    """Strip any accidental markdown fences and parse the JSON reply."""
    cleaned = raw_reply.strip().replace("```json", "").replace("```", "").strip()
    result = json.loads(cleaned)
    # Make sure every expected key exists, just in case
    result.setdefault("category", "Safe")
    result.setdefault("risk_level", "Safe")
    result.setdefault("risk_score", 0)
    result.setdefault("reason", "")
    result.setdefault("suggestion", SUGGESTIONS.get(result["category"], SUGGESTIONS["Safe"]))
    return result


# ---------------------------------------------------------------------
# 3. PUBLIC FUNCTION used by app.py
# ---------------------------------------------------------------------

def analyze_text(text):
    """
    Main entry point. Tries the configured AI provider first (if any),
    and always falls back to the offline rule-based engine on any error.
    This guarantees the hackathon demo keeps working no matter what.
    """
    if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
        try:
            return _call_gemini(text)
        except Exception as e:
            print(f"[ai_analyzer] Gemini call failed, using rule-based fallback: {e}")

    elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
        try:
            return _call_openai(text)
        except Exception as e:
            print(f"[ai_analyzer] OpenAI call failed, using rule-based fallback: {e}")

    return _rule_based_analysis(text)
