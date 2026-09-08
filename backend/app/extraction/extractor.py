import re
import uuid
import logging
from typing import List, Dict, Any
from app.ai.ai_provider import get_ai_provider

logger = logging.getLogger("cybersaarthi.extractor")

class PropertyExtractor:
    REGEX_PATTERNS = {
        "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "UPI": r'[a-zA-Z0-9.\-_]{2,100}@(?!gmail|yahoo|hotmail|outlook)[a-zA-Z]{2,64}',
        "PHONE": r'(?:(?:\+|00)91[\s-]*)?[6-9]\d{9}\b',
        "TRANSACTION_ID": r'\b(?:TXN|RRN|IMPS|NEFT|UPI|REF|TRX)[0-9A-Z]{4,20}\b|\b[A-Z]{3,4}[0-9]{6,14}\b',
        "URL": r'https?://[^\s/$.?#].[^\s]*|www\.[^\s]+\.[a-z]{2,}|[a-zA-Z0-9-]+\.(?:example|com|net|org|xyz|info|online|in)(?:/[^\s]*)?',
        "IFSC": r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
        "AMOUNT": r'(?:[₹$]|Rs\.?|INR)\s*\d+(?:,\d+)*(?:\.\d{2})?',
        "SOCIAL_HANDLE": r'(?<!\w)@[A-Za-z0-9_]{3,30}\b'
    }

    @staticmethod
    def normalize_property(prop_type: str, raw_val: str) -> str:
        val = raw_val.strip()
        
        if prop_type == "UPI":
            return val.lower()
        elif prop_type == "PHONE":
            # Extract last 10 digits for Indian standard format
            digits = re.sub(r'\D', '', val)
            if len(digits) >= 10:
                return digits[-10:]
            return digits
        elif prop_type == "EMAIL":
            return val.lower()
        elif prop_type == "TRANSACTION_ID":
            return re.sub(r'[\s:-]', '', val).upper()
        elif prop_type == "URL":
            val_lower = val.lower()
            val_lower = re.sub(r'^https?://', '', val_lower)
            val_lower = re.sub(r'^www\.', '', val_lower)
            return val_lower.split('/')[0] # extract domain hostname
        elif prop_type == "IFSC":
            return val.upper()
        elif prop_type == "AMOUNT":
            # Strip symbols and leave numeric string
            nums = re.findall(r'\d+', val)
            return "".join(nums) if nums else val
        elif prop_type in ["LOCATION", "PERSON", "ORGANIZATION"]:
            return val.title()
        elif prop_type == "SOCIAL_HANDLE":
            return val.lower() if val.startswith("@") else f"@{val.lower()}"
        
        return val

    def extract_properties(self, text: str, api_key: str = "") -> List[Dict[str, Any]]:
        extracted = []
        seen_normalized = set()

        # 1. Deterministic Regex Extraction
        for ptype, pattern in self.REGEX_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                raw_val = m.group(0)
                norm_val = self.normalize_property(ptype, raw_val)
                key = f"{ptype}:{norm_val}"
                
                if key not in seen_normalized:
                    seen_normalized.add(key)
                    extracted.append({
                        "id": f"prop_{uuid.uuid4().hex[:12]}",
                        "type": ptype,
                        "raw_value": raw_val,
                        "normalized_value": norm_val,
                        "confidence": 0.99 if ptype in ["PHONE", "UPI", "EMAIL", "IFSC"] else 0.95,
                        "source": "REGEX"
                    })

        # 2. Contextual AI/NLP Extraction for LOCATION, PERSON, ORGANIZATION, DATE
        ai_provider = get_ai_provider(api_key)
        contextual = ai_provider.extract_contextual_entities(text)
        for entity in contextual:
            ptype = entity["type"]
            raw_val = entity["raw_value"]
            norm_val = self.normalize_property(ptype, raw_val)
            key = f"{ptype}:{norm_val}"
            
            if key not in seen_normalized:
                seen_normalized.add(key)
                extracted.append({
                    "id": f"prop_{uuid.uuid4().hex[:12]}",
                    "type": ptype,
                    "raw_value": raw_val,
                    "normalized_value": norm_val,
                    "confidence": entity.get("confidence", 0.90),
                    "source": entity.get("source", "AI_NLP")
                })

        return extracted

property_extractor = PropertyExtractor()
