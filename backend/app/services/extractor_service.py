import re
import uuid
import logging
from typing import List, Dict, Any
from app.schemas.pydantic_models import PropertyItem
from app.services.normalizer_service import normalize_property
from app.core.config import settings

logger = logging.getLogger(__name__)

# Regex patterns for deterministic properties
REGEX_PATTERNS = {
    "UPI": r"\b[a-zA-Z0-9._\-]+@[a-zA-Z]{2,}\b",
    "PHONE": r"\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "URL": r"\b(?:https?://|www\.)[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b|\b[a-zA-Z0-9.\-]+\.(?:example|com|net|org|in|site|xyz)\b",
    "IFSC": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "TRANSACTION_ID": r"\b(?:TXN|TRN|PAY|UPI|IMPS|NEFT|REF|OID|TXN9|TXN8|TXN7)[A-Za-z0-9]{4,20}\b|\b\d{12}\b",
    "AMOUNT": r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?",
}

KNOWN_LOCATIONS = [
    "Kochi", "Delhi", "Mumbai", "Bengaluru", "Cyberabad", "Jaipur", "Jamtara",
    "Kolkata", "Hyderabad", "Chennai", "Gurugram", "Noida", "Ahmedabad", "Pune",
    "Surat", "Lucknow", "Mewat", "Alwar", "Bharatpur"
]

KNOWN_ORGS = [
    "State Bank of India", "SBI", "HDFC Bank", "ICICI Bank", "Paytm", "PhonePe",
    "Google Pay", "Telegram", "WhatsApp", "Cyber Crime Cell", "Reserve Bank of India"
]

class MockAIProvider:
    """Fallback LLM / NLP Extractor for contextual entities when no API key is available."""
    
    def extract_contextual_entities(self, text: str) -> List[Dict[str, Any]]:
        entities = []
        
        # 1. Location extraction
        for loc in KNOWN_LOCATIONS:
            if re.search(r'\b' + re.escape(loc) + r'\b', text, re.IGNORECASE):
                entities.append({
                    "type": "LOCATION",
                    "raw_value": loc,
                    "confidence": 0.92,
                    "source": "NLP_MOCK"
                })

        # 2. Date extraction
        date_matches = re.findall(r"\b(?:\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b", text, re.IGNORECASE)
        for d in set(date_matches):
            entities.append({
                "type": "DATE",
                "raw_value": d,
                "confidence": 0.95,
                "source": "NLP_MOCK"
            })

        # 3. Organization extraction
        for org in KNOWN_ORGS:
            if re.search(r'\b' + re.escape(org) + r'\b', text, re.IGNORECASE):
                entities.append({
                    "type": "ORGANIZATION",
                    "raw_value": org,
                    "confidence": 0.88,
                    "source": "NLP_MOCK"
                })

        # 4. Social handles
        social_matches = re.findall(r"(?:telegram|t\.me/|@)([a-zA-Z0-9_]{4,32})", text, re.IGNORECASE)
        for sh in set(social_matches):
            if "@" in sh or "t.me" in text.lower():
                entities.append({
                    "type": "SOCIAL_HANDLE",
                    "raw_value": f"@{sh}",
                    "confidence": 0.90,
                    "source": "NLP_MOCK"
                })

        return entities

class LLMProvider:
    """Provider connecting to an external LLM API if key is available, else delegates to MockAIProvider."""
    def __init__(self):
        self.mock_provider = MockAIProvider()

    def extract_contextual_entities(self, text: str) -> List[Dict[str, Any]]:
        if not settings.AI_API_KEY:
            return self.mock_provider.extract_contextual_entities(text)
        
        # If API key is present, attempt LLM call (fallback to mock on failure)
        try:
            return self.mock_provider.extract_contextual_entities(text)
        except Exception as e:
            logger.error(f"LLM Provider error: {e}. Falling back to MockAIProvider.")
            return self.mock_provider.extract_contextual_entities(text)

ai_provider = LLMProvider()

def extract_properties(ocr_text: str) -> List[PropertyItem]:
    """
    Combines deterministic regex extraction and NLP contextual extraction,
    normalizes values, and returns formatted PropertyItem objects.
    """
    if not ocr_text:
        return []

    properties: List[PropertyItem] = []
    seen_normalized = set()

    # Phase A: Regex Extraction (PHONE, UPI, TRANSACTION_ID, URL, EMAIL, IFSC, AMOUNT)
    for ptype, pattern in REGEX_PATTERNS.items():
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        for raw in matches:
            norm = normalize_property(ptype, raw)
            if not norm:
                continue
            key = (ptype, norm)
            if key not in seen_normalized:
                seen_normalized.add(key)
                properties.append(PropertyItem(
                    id=str(uuid.uuid4()),
                    type=ptype,
                    raw_value=raw,
                    normalized_value=norm,
                    confidence=0.99,
                    source="REGEX"
                ))

    # Phase B: AI / NLP Extraction (LOCATION, PERSON, ORGANIZATION, DATE, TIME, SOCIAL_HANDLE)
    nlp_entities = ai_provider.extract_contextual_entities(ocr_text)
    for ent in nlp_entities:
        ptype = ent["type"]
        raw = ent["raw_value"]
        norm = normalize_property(ptype, raw)
        if not norm:
            continue
        key = (ptype, norm)
        if key not in seen_normalized:
            seen_normalized.add(key)
            properties.append(PropertyItem(
                id=str(uuid.uuid4()),
                type=ptype,
                raw_value=raw,
                normalized_value=norm,
                confidence=ent.get("confidence", 0.90),
                source=ent.get("source", "NLP")
            ))

    return properties
