"""
chatbot.py
----------
A simple "AI Safety Assistant" parents can ask questions to, e.g.
"What should I do if my child receives bullying messages?"

Like ai_analyzer.py, this tries a real AI API if one is configured,
and otherwise answers from a small built-in FAQ so the chatbot
always has *something* useful to say during the demo.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "none").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SYSTEM_CONTEXT = (
    "You are a kind, practical child-online-safety assistant for parents. "
    "Give short, clear, actionable advice in 3-5 sentences. Avoid jargon."
)

# Built-in answers for common questions (keyword matched)
FAQ = {
    "bully": "Stay calm and talk to your child without judgment first. Save screenshots of the messages as evidence, then report/block the sender on the platform. If it continues or feels serious, involve the school or local authorities.",
    "stranger": "Teach your child to never share personal details (address, school, phone number) with people they only know online. Review their friend/follower lists together and remove unknown contacts.",
    "adult content": "Turn on platform-level content restrictions and have an honest, age-appropriate conversation. Avoid shaming your child -- curiosity is normal, and an open conversation keeps them coming to you in future.",
    "scam": "Never click suspicious links. Teach your child the signs of a scam: urgency, prizes they didn't enter for, and requests for passwords or money. Verify with you before acting on any such message.",
    "password": "Help your child set strong, unique passwords and turn on two-factor authentication where possible. Never share passwords with online 'friends', even trusted-seeming ones.",
    "screen time": "Set clear, consistent screen-time limits together with your child rather than imposing them unilaterally -- this improves cooperation. Use built-in device screen-time tools to enforce the agreed limits.",
    "report": "Most apps have a built-in 'Report' button on messages/profiles. Use it, then block the user. Keep a screenshot in case the school or police need it later.",
}

DEFAULT_ANSWER = (
    "That's an important question. In general: stay calm, keep communication "
    "open with your child, save evidence of anything concerning, use the "
    "platform's report/block tools, and involve a trusted adult or authority "
    "if the situation feels serious. Ask me something more specific and I "
    "can give more targeted advice!"
)


def _faq_answer(question):
    q = question.lower()
    for keyword, answer in FAQ.items():
        if keyword in q:
            return answer
    return DEFAULT_ANSWER


def _call_gemini(question):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    prompt = f"{SYSTEM_CONTEXT}\n\nParent's question: {question}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai(question):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_CONTEXT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.4,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def get_answer(question):
    """Return an answer to the parent's question, AI-backed if configured."""
    if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
        try:
            return _call_gemini(question)
        except Exception as e:
            print(f"[chatbot] Gemini call failed, using FAQ fallback: {e}")

    elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
        try:
            return _call_openai(question)
        except Exception as e:
            print(f"[chatbot] OpenAI call failed, using FAQ fallback: {e}")

    return _faq_answer(question)
