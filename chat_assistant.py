

# """
# Module 2: AI Health Chat Assistant
# -----------------------------------
# After Module 1 predicts a disease, this module lets the user ask
# follow-up questions like:
#   - "Why did I get Flu?"
#   - "What foods should I eat?"
#   - "Can I go to college?"
#   - "What medicines are usually prescribed?"

# Design:
#   1. Try the Gemini LLM first (grounded with a disease knowledge base
#      in the prompt, so it doesn't hallucinate medical facts).
#   2. If the LLM call fails (no API key, network error, quota hit),
#      fall back to a rule-based keyword matcher using the same
#      knowledge base, so the app never breaks in a demo.

# IMPORTANT: this gives general educational information only, not a
# diagnosis or a prescription. Every response should tell the user to
# confirm with a real doctor for anything specific to their case.
# """

# import os
# import re
# from google import genai
# from google.genai import types

# # ---------------------------------------------------------------------------
# # 1. Knowledge base
# # ---------------------------------------------------------------------------
# # Keep this deliberately general (food categories, activity guidance, classes
# # of medicine) rather than specific doses or brand names. A doctor decides
# # the specifics; this app should never sound like it's prescribing.

# DISEASE_KB = {
#     "Flu": {
#         "why": "Flu is usually flagged when symptoms like fever, body ache, "
#                "fatigue, and cough appear together, which is the classic "
#                "influenza symptom cluster.",
#         "foods_to_eat": ["warm fluids (soup, herbal tea)", "fruits high in vitamin C",
#                           "easily digestible foods like khichdi or porridge"],
#         "foods_to_avoid": ["cold drinks", "fried/oily food", "alcohol"],
#         "activity_advice": "Rest is recommended. Avoid college/work until fever-free "
#                             "for at least 24 hours to avoid spreading it to others.",
#         "medicine_classes": "Doctors commonly consider antipyretics (fever reducers) "
#                              "and rest/fluids. Always confirm the exact medicine and "
#                              "dose with a doctor or pharmacist.",
#     },
#     "COVID": {
#         "why": "COVID is often flagged when symptoms include fever, dry cough, "
#                "fatigue, and sometimes loss of taste/smell.",
#         "foods_to_eat": ["warm fluids", "protein-rich food to support recovery",
#                           "fruits high in vitamin C and zinc"],
#         "foods_to_avoid": ["cold drinks", "smoking/vaping", "alcohol"],
#         "activity_advice": "Isolation is recommended per local health guidelines. "
#                             "Avoid college/work and follow your local health authority's "
#                             "isolation period.",
#         "medicine_classes": "Doctors commonly consider antipyretics for fever and "
#                              "monitor oxygen levels for severe cases. Always confirm "
#                              "with a doctor, especially if breathing difficulty occurs.",
#     },
#     "Common Cold": {
#         "why": "A Common Cold is usually flagged with milder symptoms like "
#                "sneezing, runny nose, and mild sore throat, without high fever.",
#         "foods_to_eat": ["warm soups", "citrus fruits", "ginger/honey tea"],
#         "foods_to_avoid": ["cold drinks", "very oily food"],
#         "activity_advice": "Usually safe to attend college/work if you feel up to it "
#                             "and don't have a fever, but consider a mask to avoid "
#                             "spreading it.",
#         "medicine_classes": "Doctors commonly consider antihistamines or decongestants. "
#                              "Always confirm the exact medicine and dose with a doctor "
#                              "or pharmacist.",
#     },
#     # Add more diseases here to match whatever your Module 1 dataset predicts.
# }

# GENERAL_DISCLAIMER = (
#     "This is general information, not a medical diagnosis or prescription. "
#     "Please confirm anything specific to your case with a doctor."
# )

# # ---------------------------------------------------------------------------
# # 2. Gemini LLM call
# # ---------------------------------------------------------------------------

# _client = None


# def _get_client():
#     global _client
#     if _client is None:
#         api_key = os.getenv("GEMINI_API_KEY")
#         if not api_key:
#             raise RuntimeError("GEMINI_API_KEY not set in environment")
#         _client = genai.Client(api_key=api_key)
#     return _client


# def get_llm_response(question: str, disease: str, symptoms: list[str] | None = None) -> str:
#     """
#     Ask Gemini, grounded with the knowledge-base facts for this disease so it
#     can't hallucinate dosages or contradict the app's own data.
#     Raises on any failure -- caller is expected to catch and fall back.
#     """
#     client = _get_client()

#     kb_entry = DISEASE_KB.get(disease, {})
#     symptoms_str = ", ".join(symptoms) if symptoms else "not provided"

#     system_context = f"""You are a friendly health information assistant inside a
# student healthcare app called MedAssist AI. The user's app predicted: {disease}.
# Reported symptoms: {symptoms_str}.

# Known reference facts about this condition (use these, don't contradict them):
# - Why it's usually flagged: {kb_entry.get('why', 'N/A')}
# - Foods generally recommended: {kb_entry.get('foods_to_eat', 'N/A')}
# - Foods generally to avoid: {kb_entry.get('foods_to_avoid', 'N/A')}
# - Activity guidance: {kb_entry.get('activity_advice', 'N/A')}
# - Medicine classes doctors commonly consider: {kb_entry.get('medicine_classes', 'N/A')}

# Rules:
# - Give general, educational information only. Never give a specific dose or brand recommendation.
# - Keep the answer short (2-4 sentences).
# - Always end by encouraging the user to confirm with a real doctor for anything specific to them.
# - Do not diagnose beyond what the app already predicted.
# """

#     # response = client.models.generate_content(
#     #     model="gemini-3.5-flash",
#     #     contents=question,
#     #     config=types.GenerateContentConfig(system_instruction=system_context),
#     # )
#     # return response.text.strip()
#     response = client.models.generate_content(
#         model="gemini-3.5-flash",
#         contents=question,
#         config=types.GenerateContentConfig(
#             system_instruction=system_context,
#             request_options={"timeout": 8},  # seconds -- fail fast, fall back quickly
#         ),
#     )
#     return response.text.strip()


# # ---------------------------------------------------------------------------
# # 3. Rule-based fallback
# # ---------------------------------------------------------------------------

# _INTENT_PATTERNS = {
#     "why": [r"\bwhy\b", r"\breason\b", r"\bhow come\b"],
#     "foods_to_eat": [r"\bwhat.*eat\b", r"\bfood\b.*\brecommend\b", r"\bdiet\b", r"\bshould i eat\b"],
#     "foods_to_avoid": [r"\bavoid\b.*\bfood\b", r"\bnot eat\b", r"\bwhat.*avoid\b"],
#     "activity_advice": [r"\bcollege\b", r"\bwork\b", r"\bschool\b", r"\bgo out\b", r"\btravel\b"],
#     "medicine_classes": [r"\bmedicine\b", r"\bmedication\b", r"\bdrug\b", r"\bprescri\b", r"\btablet\b"],
#     "severity": [r"\bdangerous\b", r"\bserious\b", r"\bsevere\b", r"\brisky\b", r"\bworried\b", r"\bshould i worry\b"],
#     "gratitude": [r"\bthank", r"\bthanks\b", r"\bappreciate\b"],
# }
# _GENERIC_FALLBACKS = {
#     "why": "This was flagged based on the combination of symptoms you reported matching a known pattern for this condition.",
#     "foods_to_eat": "In general, staying hydrated and eating light, nutritious meals supports recovery from most conditions.",
#     "foods_to_avoid": "In general, it's wise to avoid processed food, excess sugar, alcohol, and smoking while unwell.",
#     "activity_advice": "It's best to rest and avoid strenuous activity or attending college/work until you've been evaluated, especially if symptoms are new or worsening.",
#     "medicine_classes": "Only a doctor can safely recommend specific medicines for this condition based on a proper examination.",
#     "severity": "Severity can vary a lot from person to person, so it's not something this app can judge reliably. If your symptoms are severe, worsening, or worrying you, please see a doctor soon rather than waiting.",
#     "gratitude": "You're welcome! Take care of yourself, and don't hesitate to check in with a doctor if anything changes.",
# }


# # def get_rule_based_response(question: str, disease: str) -> str:
# #     """Simple keyword matcher over the knowledge base. Used when the LLM
# #     is unavailable, so the app degrades gracefully instead of crashing."""
# #     kb_entry = DISEASE_KB.get(disease)
# #     if not kb_entry:
# #         return (f"I don't have detailed information for '{disease}' yet. "
# #                 f"{GENERAL_DISCLAIMER}")

# #     q = question.lower()
# #     for intent, patterns in _INTENT_PATTERNS.items():
# #         if any(re.search(p, q) for p in patterns):
# #             value = kb_entry[intent]
# #             if isinstance(value, list):
# #                 value = ", ".join(value)
# #             return f"{value} {GENERAL_DISCLAIMER}"

# #     # No pattern matched -- give a general summary instead of a dead end.
# #     return (f"For {disease}: {kb_entry['why']} {GENERAL_DISCLAIMER}")
# def get_rule_based_response(question: str, disease: str) -> str:
#     """Simple keyword matcher over the knowledge base. Used when the LLM
#     is unavailable, so the app degrades gracefully instead of crashing."""
#     kb_entry = DISEASE_KB.get(disease)
#     q = question.lower()

#     if not kb_entry:
#         # No specific data for this disease -- still give a useful,
#         # intent-aware generic answer instead of a dead end.
#         # for intent, patterns in _INTENT_PATTERNS.items():
#         #     if any(re.search(p, q) for p in patterns):
#         #         generic = _GENERIC_FALLBACKS[intent]
#         #         return f"{generic} {GENERAL_DISCLAIMER}"
#         for intent, patterns in _INTENT_PATTERNS.items():
#             if any(re.search(p, q) for p in patterns):
#                 generic = _GENERIC_FALLBACKS[intent]
#                 if intent == "gratitude":
#                     return generic
#                 return f"{generic} {GENERAL_DISCLAIMER}"
#         return (f"I don't have detailed reference info for '{disease}' yet, "
#                 f"but it's important to get it evaluated properly. {GENERAL_DISCLAIMER}")

#     for intent, patterns in _INTENT_PATTERNS.items():
#         if any(re.search(p, q) for p in patterns):
#             value = kb_entry[intent]
#             if isinstance(value, list):
#                 value = ", ".join(value)
#             return f"{value} {GENERAL_DISCLAIMER}"

#     return (f"For {disease}: {kb_entry['why']} {GENERAL_DISCLAIMER}")


# # ---------------------------------------------------------------------------
# # 4. Orchestrator -- this is what your Flask route should call
# # ---------------------------------------------------------------------------

# def get_chat_response(question: str, disease: str, symptoms: list[str] | None = None,
#                        use_llm: bool = True) -> dict:
#     """
#     Returns: {"answer": str, "source": "llm" | "rule_based"}
#     """
#     if use_llm:
#         try:
#             answer = get_llm_response(question, disease, symptoms)
#             return {"answer": answer, "source": "llm"}
#         except Exception as e:
#             # Log this in a real app; falling through to rule-based on purpose.
#             print(f"[chat_assistant] LLM call failed, using fallback: {e}")

#     answer = get_rule_based_response(question, disease)
#     return {"answer": answer, "source": "rule_based"}

"""
Module 2: AI Health Chat Assistant
-----------------------------------
After Module 1 predicts a disease, this module lets the user ask
follow-up questions like:
  - "Why did I get Flu?"
  - "What foods should I eat?"
  - "Can I go to college?"
  - "What medicines are usually prescribed?"

Design:
  1. Try the Gemini LLM first (grounded with a disease knowledge base
     in the prompt, so it doesn't hallucinate medical facts).
  2. If the LLM call fails (no API key, network error, quota hit,
     timeout), fall back to a rule-based keyword matcher using the
     same knowledge base, so the app never breaks in a demo or in
     production.

IMPORTANT: this gives general educational information only, not a
diagnosis or a prescription. Every response should tell the user to
confirm with a real doctor for anything specific to their case.
"""

import logging
import os
import re

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Knowledge base
# ---------------------------------------------------------------------------
# Keep this deliberately general (food categories, activity guidance, classes
# of medicine) rather than specific doses or brand names. A doctor decides
# the specifics; this app should never sound like it's prescribing.

DISEASE_KB = {
    "Flu": {
        "why": "Flu is usually flagged when symptoms like fever, body ache, "
               "fatigue, and cough appear together, which is the classic "
               "influenza symptom cluster.",
        "foods_to_eat": ["warm fluids (soup, herbal tea)", "fruits high in vitamin C",
                          "easily digestible foods like khichdi or porridge"],
        "foods_to_avoid": ["cold drinks", "fried/oily food", "alcohol"],
        "activity_advice": "Rest is recommended. Avoid college/work until fever-free "
                            "for at least 24 hours to avoid spreading it to others.",
        "medicine_classes": "Doctors commonly consider antipyretics (fever reducers) "
                             "and rest/fluids. Always confirm the exact medicine and "
                             "dose with a doctor or pharmacist.",
    },
    "COVID": {
        "why": "COVID is often flagged when symptoms include fever, dry cough, "
               "fatigue, and sometimes loss of taste/smell.",
        "foods_to_eat": ["warm fluids", "protein-rich food to support recovery",
                          "fruits high in vitamin C and zinc"],
        "foods_to_avoid": ["cold drinks", "smoking/vaping", "alcohol"],
        "activity_advice": "Isolation is recommended per local health guidelines. "
                            "Avoid college/work and follow your local health authority's "
                            "isolation period.",
        "medicine_classes": "Doctors commonly consider antipyretics for fever and "
                             "monitor oxygen levels for severe cases. Always confirm "
                             "with a doctor, especially if breathing difficulty occurs.",
    },
    "Common Cold": {
        "why": "A Common Cold is usually flagged with milder symptoms like "
               "sneezing, runny nose, and mild sore throat, without high fever.",
        "foods_to_eat": ["warm soups", "citrus fruits", "ginger/honey tea"],
        "foods_to_avoid": ["cold drinks", "very oily food"],
        "activity_advice": "Usually safe to attend college/work if you feel up to it "
                            "and don't have a fever, but consider a mask to avoid "
                            "spreading it.",
        "medicine_classes": "Doctors commonly consider antihistamines or decongestants. "
                             "Always confirm the exact medicine and dose with a doctor "
                             "or pharmacist.",
    },
    # Add more diseases here to match whatever your Module 1 dataset predicts.
}

GENERAL_DISCLAIMER = (
    "This is general information, not a medical diagnosis or prescription. "
    "Please confirm anything specific to your case with a doctor."
)

# Gemini model to use. Pin an explicit, dated/stable string in production
# rather than a "-latest" alias so a Google-side model swap can't silently
# change your app's behavior. Update this constant when you deliberately
# want to move to a newer model.
GEMINI_MODEL = "gemini-3.5-flash"

# How long to wait for the LLM before giving up and using the rule-based
# fallback. google-genai's HttpOptions.timeout is in MILLISECONDS.
LLM_TIMEOUT_MS = 12_000  # API enforces a 10s minimum; padding above it

# ---------------------------------------------------------------------------
# 2. Gemini LLM call
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        _client = genai.Client(api_key=api_key)
    return _client


def _build_system_context(disease: str, symptoms: list[str] | None) -> str:
    kb_entry = DISEASE_KB.get(disease)
    symptoms_str = ", ".join(symptoms) if symptoms else "not provided"

    if kb_entry is None:
        # No local reference facts for this disease -- don't hand the model
        # a prompt full of "N/A" fields. Let it answer generally, still under
        # the same safety rules.
        return f"""You are a friendly health information assistant inside a
student healthcare app called MedAssist AI. The user's app predicted: {disease}.
Reported symptoms: {symptoms_str}.

There is no internal reference entry for this specific condition, so rely on
your general medical knowledge, but stay conservative and generic.

Rules:
- Give general, educational information only. Never give a specific dose or brand recommendation.
- Keep the answer short (2-4 sentences).
- Always end by encouraging the user to confirm with a real doctor for anything specific to them.
- Do not diagnose beyond what the app already predicted.
"""

    return f"""You are a friendly health information assistant inside a
student healthcare app called MedAssist AI. The user's app predicted: {disease}.
Reported symptoms: {symptoms_str}.

Known reference facts about this condition (use these, don't contradict them):
- Why it's usually flagged: {kb_entry['why']}
- Foods generally recommended: {kb_entry['foods_to_eat']}
- Foods generally to avoid: {kb_entry['foods_to_avoid']}
- Activity guidance: {kb_entry['activity_advice']}
- Medicine classes doctors commonly consider: {kb_entry['medicine_classes']}

Rules:
- Give general, educational information only. Never give a specific dose or brand recommendation.
- Keep the answer short (2-4 sentences).
- Always end by encouraging the user to confirm with a real doctor for anything specific to them.
- Do not diagnose beyond what the app already predicted.
"""


def get_llm_response(question: str, disease: str, symptoms: list[str] | None = None) -> str:
    """
    Ask Gemini, grounded with the knowledge-base facts for this disease so it
    can't hallucinate dosages or contradict the app's own data.
    Raises on any failure -- caller is expected to catch and fall back.
    """
    client = _get_client()
    system_context = _build_system_context(disease, symptoms)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_context,
            # Correct way to set a per-call timeout on the google-genai SDK.
            # NOTE: this is in milliseconds, and older SDK docs/snippets that
            # use `request_options={"timeout": <seconds>}` are for the
            # deprecated `google.generativeai` package -- passing that kwarg
            # here raises a validation error on every call.
            http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
        ),
    )

    text = (response.text or "").strip()
    if not text:
        # Some SDK responses can come back empty (e.g. safety filtering,
        # truncation) without raising -- treat that as a failure too so we
        # fall back instead of returning a blank message to the user.
        raise ValueError("Empty response from Gemini")
    return text


# ---------------------------------------------------------------------------
# 3. Rule-based fallback
# ---------------------------------------------------------------------------

_INTENT_PATTERNS = {
    "why": [r"\bwhy\b", r"\breason\b", r"\bhow come\b"],
    "foods_to_eat": [r"\bwhat.*eat\b", r"\bfood\b.*\brecommend\b", r"\bdiet\b", r"\bshould i eat\b"],
    "foods_to_avoid": [r"\bavoid\b.*\bfood\b", r"\bnot eat\b", r"\bwhat.*avoid\b"],
    "activity_advice": [r"\bcollege\b", r"\bwork\b", r"\bschool\b", r"\bgo out\b", r"\btravel\b"],
    "medicine_classes": [r"\bmedicine\b", r"\bmedication\b", r"\bdrug\b", r"\bprescri\b", r"\btablet\b"],
    "severity": [r"\bdangerous\b", r"\bserious\b", r"\bsevere\b", r"\brisky\b", r"\bworried\b", r"\bshould i worry\b"],
    "gratitude": [r"\bthank", r"\bthanks\b", r"\bappreciate\b"],
}

# Generic, disease-agnostic answers for intents that aren't part of each
# DISEASE_KB entry (severity/gratitude), and for diseases with no KB entry
# at all. Keyed the same as _INTENT_PATTERNS so both code paths can share
# this dict safely.
_GENERIC_FALLBACKS = {
    "why": "This was flagged based on the combination of symptoms you reported matching a known pattern for this condition.",
    "foods_to_eat": "In general, staying hydrated and eating light, nutritious meals supports recovery from most conditions.",
    "foods_to_avoid": "In general, it's wise to avoid processed food, excess sugar, alcohol, and smoking while unwell.",
    "activity_advice": "It's best to rest and avoid strenuous activity or attending college/work until you've been evaluated, especially if symptoms are new or worsening.",
    "medicine_classes": "Only a doctor can safely recommend specific medicines for this condition based on a proper examination.",
    "severity": "Severity can vary a lot from person to person, so it's not something this app can judge reliably. If your symptoms are severe, worsening, or worrying you, please see a doctor soon rather than waiting.",
    "gratitude": "You're welcome! Take care of yourself, and don't hesitate to check in with a doctor if anything changes.",
}

# Intents that are never present as keys inside a DISEASE_KB entry, so they
# should always be answered from _GENERIC_FALLBACKS even when the disease
# is known.
_DISEASE_AGNOSTIC_INTENTS = {"severity", "gratitude"}


def get_rule_based_response(question: str, disease: str) -> str:
    """Simple keyword matcher over the knowledge base. Used when the LLM
    is unavailable, so the app degrades gracefully instead of crashing."""
    kb_entry = DISEASE_KB.get(disease)
    q = question.lower()

    for intent, patterns in _INTENT_PATTERNS.items():
        if not any(re.search(p, q) for p in patterns):
            continue

        # Gratitude doesn't need the disclaimer tacked on.
        if intent == "gratitude":
            return _GENERIC_FALLBACKS["gratitude"]

        # Severity, and any disease we have no KB entry for, always use the
        # generic answer -- DISEASE_KB entries don't define a "severity" key,
        # so indexing kb_entry["severity"] would raise a KeyError.
        if kb_entry is None or intent in _DISEASE_AGNOSTIC_INTENTS:
            return f"{_GENERIC_FALLBACKS[intent]} {GENERAL_DISCLAIMER}"

        value = kb_entry[intent]
        if isinstance(value, list):
            value = ", ".join(value)
        return f"{value} {GENERAL_DISCLAIMER}"

    # No pattern matched.
    if kb_entry is None:
        return (f"I don't have detailed reference info for '{disease}' yet, "
                f"but it's important to get it evaluated properly. {GENERAL_DISCLAIMER}")
    return f"For {disease}: {kb_entry['why']} {GENERAL_DISCLAIMER}"


# ---------------------------------------------------------------------------
# 4. Orchestrator -- this is what your Flask route should call
# ---------------------------------------------------------------------------

def get_chat_response(question: str, disease: str, symptoms: list[str] | None = None,
                       use_llm: bool = True) -> dict:
    """
    Returns: {"answer": str, "source": "llm" | "rule_based"}
    """
    if use_llm:
        try:
            answer = get_llm_response(question, disease, symptoms)
            return {"answer": answer, "source": "llm"}
        except Exception:
            # Falling through to rule-based on purpose. Logged with full
            # traceback so a misconfigured client (bad API key, wrong SDK
            # kwarg, etc.) is visible in production instead of silently
            # degrading forever.
            logger.exception(
                "LLM call failed for disease=%r, question=%r -- using rule-based fallback",
                disease, question,
            )

    answer = get_rule_based_response(question, disease)
    return {"answer": answer, "source": "rule_based"}