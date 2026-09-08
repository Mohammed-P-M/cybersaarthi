import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("cybersaarthi.ai")

class BaseAIProvider:
    def extract_contextual_entities(self, text: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class MockAIProvider(BaseAIProvider):
    """Fallback AI provider when AI_API_KEY is missing or offline."""
    def extract_contextual_entities(self, text: str) -> List[Dict[str, Any]]:
        results = []
        text_lower = text.lower()
        
        # Check for known demo / common Indian location names
        locations = ["kochi", "bengaluru", "bangalore", "mumbai", "delhi", "hyderabad", "chennai", "kolkata", "pune", "ahmedabad", "jaipur", "thiruvananthapuram", "kozhikode"]
        for loc in locations:
            if loc in text_lower:
                results.append({
                    "type": "LOCATION",
                    "raw_value": loc.capitalize(),
                    "normalized_value": loc.capitalize(),
                    "confidence": 0.92,
                    "source": "MOCK_AI"
                })
        
        # Check for organizations
        orgs = ["sbi", "hdfc", "icici", "paytm", "phonepe", "gpay", "google pay", "amazon pay", "axis bank"]
        for org in orgs:
            if org in text_lower:
                results.append({
                    "type": "ORGANIZATION",
                    "raw_value": org.upper(),
                    "normalized_value": org.upper(),
                    "confidence": 0.90,
                    "source": "MOCK_AI"
                })
                
        # Check for potential names / person entities
        if "account holder:" in text_lower or "name:" in text_lower or "to:" in text_lower:
            # Simple heuristic mock extraction
            lines = text.splitlines()
            for line in lines:
                if any(kw in line.lower() for kw in ["name:", "account holder:", "to:"]):
                    val = line.split(":", 1)[-1].strip()
                    if val and len(val) < 40 and not "@" in val and not val.isdigit():
                        results.append({
                            "type": "PERSON",
                            "raw_value": val,
                            "normalized_value": val.title(),
                            "confidence": 0.85,
                            "source": "MOCK_AI"
                        })

        return results

class LLMProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def extract_contextual_entities(self, text: str) -> List[Dict[str, Any]]:
        # If no key, fallback to mock
        if not self.api_key:
            return MockAIProvider().extract_contextual_entities(text)
        
        # Simple simulated LLM response structure for structured extraction
        try:
            # Here we can call Gemini or OpenAI API if configured
            return MockAIProvider().extract_contextual_entities(text)
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return MockAIProvider().extract_contextual_entities(text)

def get_ai_provider(api_key: str = "") -> BaseAIProvider:
    if api_key:
        return LLMProvider(api_key)
    return MockAIProvider()
