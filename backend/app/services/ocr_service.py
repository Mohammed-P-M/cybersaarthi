import logging

logger = logging.getLogger("cybersaarthi.ocr.legacy")


class OCRProcessingError(RuntimeError):
    pass


# This legacy module intentionally contains no synthetic OCR fallback.
# The active implementation lives in app.ocr.ocr_service.

def extract_ocr_text(file_path: str) -> str:
    raise OCRProcessingError(
        "Legacy OCR service is disabled. Use app.ocr.ocr_service.extract_text so OCR failures are reported instead of fabricated."
    )
