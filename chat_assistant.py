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
# import google.generativeai as genai

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

# _GEMINI_CONFIGURED = False


# def _ensure_gemini_configured():
#     global _GEMINI_CONFIGURED
#     if _GEMINI_CONFIGURED:
#         return
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("GEMINI_API_KEY not set in environment")
#     genai.configure(api_key=api_key)
#     _GEMINI_CONFIGURED = True


# def get_llm_response(question: str, disease: str, symptoms: list[str] | None = None) -> str:
#     """
#     Ask Gemini, grounded with the knowledge-base facts for this disease so it
#     can't hallucinate dosages or contradict the app's own data.
#     Raises on any failure -- caller is expected to catch and fall back.
#     """
#     _ensure_gemini_configured()

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

#     model = genai.GenerativeModel(
#         model_name="gemini-1.5-flash",
#         system_instruction=system_context,
#     )
#     response = model.generate_content(question)
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
# }


# def get_rule_based_response(question: str, disease: str) -> str:
#     """Simple keyword matcher over the knowledge base. Used when the LLM
#     is unavailable, so the app degrades gracefully instead of crashing."""
#     kb_entry = DISEASE_KB.get(disease)
#     if not kb_entry:
#         return (f"I don't have detailed information for '{disease}' yet. "
#                 f"{GENERAL_DISCLAIMER}")

#     q = question.lower()
#     for intent, patterns in _INTENT_PATTERNS.items():
#         if any(re.search(p, q) for p in patterns):
#             value = kb_entry[intent]
#             if isinstance(value, list):
#                 value = ", ".join(value)
#             return f"{value} {GENERAL_DISCLAIMER}"

#     # No pattern matched -- give a general summary instead of a dead end.
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
  2. If the LLM call fails (no API key, network error, quota hit),
     fall back to a rule-based keyword matcher using the same
     knowledge base, so the app never breaks in a demo.

IMPORTANT: this gives general educational information only, not a
diagnosis or a prescription. Every response should tell the user to
confirm with a real doctor for anything specific to their case.
"""

import os
import re
import google.generativeai as genai

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

# ---------------------------------------------------------------------------
# 2. Gemini LLM call
# ---------------------------------------------------------------------------

_GEMINI_CONFIGURED = False


def _ensure_gemini_configured():
    global _GEMINI_CONFIGURED
    if _GEMINI_CONFIGURED:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    genai.configure(api_key=api_key)
    _GEMINI_CONFIGURED = True


def get_llm_response(question: str, disease: str, symptoms: list[str] | None = None) -> str:
    """
    Ask Gemini, grounded with the knowledge-base facts for this disease so it
    can't hallucinate dosages or contradict the app's own data.
    Raises on any failure -- caller is expected to catch and fall back.
    """
    _ensure_gemini_configured()

    kb_entry = DISEASE_KB.get(disease, {})
    symptoms_str = ", ".join(symptoms) if symptoms else "not provided"

    system_context = f"""You are a friendly health information assistant inside a
student healthcare app called MedAssist AI. The user's app predicted: {disease}.
Reported symptoms: {symptoms_str}.

Known reference facts about this condition (use these, don't contradict them):
- Why it's usually flagged: {kb_entry.get('why', 'N/A')}
- Foods generally recommended: {kb_entry.get('foods_to_eat', 'N/A')}
- Foods generally to avoid: {kb_entry.get('foods_to_avoid', 'N/A')}
- Activity guidance: {kb_entry.get('activity_advice', 'N/A')}
- Medicine classes doctors commonly consider: {kb_entry.get('medicine_classes', 'N/A')}

Rules:
- Give general, educational information only. Never give a specific dose or brand recommendation.
- Keep the answer short (2-4 sentences).
- Always end by encouraging the user to confirm with a real doctor for anything specific to them.
- Do not diagnose beyond what the app already predicted.
"""

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_context,
    )
    response = model.generate_content(question)
    return response.text.strip()


# ---------------------------------------------------------------------------
# 3. Rule-based fallback
# ---------------------------------------------------------------------------

_INTENT_PATTERNS = {
    "why": [r"\bwhy\b", r"\breason\b", r"\bhow come\b"],
    "foods_to_eat": [r"\bwhat.*eat\b", r"\bfood\b.*\brecommend\b", r"\bdiet\b", r"\bshould i eat\b"],
    "foods_to_avoid": [r"\bavoid\b.*\bfood\b", r"\bnot eat\b", r"\bwhat.*avoid\b"],
    "activity_advice": [r"\bcollege\b", r"\bwork\b", r"\bschool\b", r"\bgo out\b", r"\btravel\b"],
    "medicine_classes": [r"\bmedicine\b", r"\bmedication\b", r"\bdrug\b", r"\bprescri\b", r"\btablet\b"],
}


def get_rule_based_response(question: str, disease: str) -> str:
    """Simple keyword matcher over the knowledge base. Used when the LLM
    is unavailable, so the app degrades gracefully instead of crashing."""
    kb_entry = DISEASE_KB.get(disease)
    if not kb_entry:
        return (f"I don't have detailed information for '{disease}' yet. "
                f"{GENERAL_DISCLAIMER}")

    q = question.lower()
    for intent, patterns in _INTENT_PATTERNS.items():
        if any(re.search(p, q) for p in patterns):
            value = kb_entry[intent]
            if isinstance(value, list):
                value = ", ".join(value)
            return f"{value} {GENERAL_DISCLAIMER}"

    # No pattern matched -- give a general summary instead of a dead end.
    return (f"For {disease}: {kb_entry['why']} {GENERAL_DISCLAIMER}")


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
        except Exception as e:
            # Log this in a real app; falling through to rule-based on purpose.
            print(f"[chat_assistant] LLM call failed, using fallback: {e}")

    answer = get_rule_based_response(question, disease)
    return {"answer": answer, "source": "rule_based"}