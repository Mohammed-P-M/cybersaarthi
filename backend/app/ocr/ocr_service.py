import os
# Work around a known PaddlePaddle 3.3.x + oneDNN/PIR incompatibility
# affecting some PP-OCRv5/PP-LCNet models.
os.environ.setdefault("FLAGS_enable_pir_api", "0")

import logging
import tempfile

logger = logging.getLogger("cybersaarthi.ocr")


class OCRProcessingError(RuntimeError):
    """Raised when evidence cannot be OCR-processed reliably."""


class OCRService:
    def __init__(self):
        self.ocr_engine = None
        self._init_ocr()

    def _init_ocr(self):
        try:
            from paddleocr import PaddleOCR

            # PaddleOCR 3.x: disable optional document preprocessing so the
            # service only downloads/runs the text OCR pipeline needed here.
            self.ocr_engine = PaddleOCR(
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name="PP-OCRv5_mobile_rec",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                enable_mkldnn=False,
                lang="en",
            )
            logger.info("PaddleOCR engine initialized successfully.")
        except TypeError:
            # Compatibility with older PaddleOCR releases. This is a real
            # OCR engine path; there is deliberately no synthetic-text fallback.
            try:
                from paddleocr import PaddleOCR
                self.ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")
                logger.info("PaddleOCR legacy engine initialized successfully.")
            except Exception as exc:
                self.ocr_engine = None
                logger.error("PaddleOCR initialization failed: %s", exc)
        except Exception as exc:
            self.ocr_engine = None
            logger.error("PaddleOCR initialization failed: %s", exc)

    @staticmethod
    def _extract_v3_text(results) -> str:
        lines = []
        for result in results or []:
            payload = None

            # PaddleOCR 3.x OCRResult behaves like a mapping and contains
            # rec_texts. Its JSON representation also exposes the same field.
            try:
                payload = result.get("rec_texts")
            except Exception:
                payload = None

            if payload is None:
                try:
                    data = result.json if not callable(result.json) else result.json()
                    payload = data.get("res", {}).get("rec_texts")
                except Exception:
                    payload = None

            if payload:
                lines.extend(str(text).strip() for text in payload if str(text).strip())

        return "\n".join(lines).strip()

    @staticmethod
    def _extract_legacy_text(result) -> str:
        lines = []
        if not result:
            return ""
        for page in result:
            if not page:
                continue
            for line in page:
                try:
                    text = line[1][0]
                except (IndexError, KeyError, TypeError):
                    continue
                if text and str(text).strip():
                    lines.append(str(text).strip())
        return "\n".join(lines).strip()

    def extract_text(self, file_bytes: bytes, file_name: str) -> str:
        """Run real OCR and fail loudly when OCR cannot produce text.

        This method intentionally never invents text. A failed OCR operation
        raises OCRProcessingError so the API can reject the submission instead
        of storing fabricated indicators.
        """
        if not file_bytes:
            raise OCRProcessingError("OCR failed: the uploaded evidence file is empty.")
        if not self.ocr_engine:
            raise OCRProcessingError(
                "OCR is unavailable: PaddleOCR could not initialize its models. "
                "Please check the OCR model download/network configuration and try again."
            )

        suffix = os.path.splitext(file_name or "evidence.jpg")[1] or ".jpg"
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="cybersaarthi_", suffix=suffix, delete=False) as tmp:
                tmp.write(file_bytes)
                temp_path = tmp.name

            # PaddleOCR 3.x uses predict(); older releases use ocr().
            if hasattr(self.ocr_engine, "predict"):
                results = self.ocr_engine.predict(temp_path)
                text = self._extract_v3_text(results)
            else:
                results = self.ocr_engine.ocr(temp_path, cls=True)
                text = self._extract_legacy_text(results)

            if not text:
                raise OCRProcessingError(
                    "OCR completed but no readable text was detected in the uploaded evidence."
                )

            logger.info("OCR extracted %d characters from %s", len(text), file_name or "evidence")
            return text

        except OCRProcessingError:
            raise
        except Exception as exc:
            logger.exception("PaddleOCR processing failed for %s", file_name or "evidence")
            raise OCRProcessingError(f"OCR failed while processing the evidence: {exc}") from exc
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    logger.warning("Could not remove temporary OCR file: %s", temp_path)


ocr_service = OCRService()
