"""
ocr_reader.py — PDF OCR Extraction Module
------------------------------------------
Converts each PDF page to an image, applies preprocessing for better
OCR accuracy on handwritten notes, and extracts text using Tesseract.

Pipeline:
  PDF → page images → preprocessing → Tesseract OCR → list of (page_num, text)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _import_dependencies():
    """
    Lazily import heavy OCR dependencies and give helpful error messages
    if any are missing.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        logger.error("pdf2image not installed. Run: pip install pdf2image")
        sys.exit(1)

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.error("pytesseract or Pillow not installed. Run: pip install pytesseract Pillow")
        sys.exit(1)

    try:
        import cv2
    except ImportError:
        logger.warning("opencv-python not installed — skipping image preprocessing. "
                       "For better OCR on handwriting, run: pip install opencv-python")
        cv2 = None

    return convert_from_path, pytesseract, Image, cv2


def _preprocess_image_for_ocr(pil_image, cv2):
    """
    Apply image preprocessing to improve Tesseract accuracy on handwritten text.

    Techniques used:
      1. Convert to grayscale
      2. Apply Otsu's adaptive thresholding (binarization)
      3. Light deskew via rotation detection

    Args:
        pil_image: A PIL Image object.
        cv2: The OpenCV module (or None if unavailable).

    Returns:
        A preprocessed PIL Image ready for Tesseract.
    """
    from PIL import Image as PILImage

    if cv2 is None:
        # No OpenCV — return image as-is (Tesseract handles basic images)
        return pil_image

    # Convert PIL → NumPy array for OpenCV processing
    img_array = np.array(pil_image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # Step 1: Grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Step 2: Denoise (helps with scan artifacts and pencil strokes)
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # Step 3: Adaptive thresholding — handles uneven lighting in handwritten notes
    binarized = cv2.adaptiveThreshold(
        denoised,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=31,   # Larger block = better for varied stroke widths
        C=10
    )

    # Step 4: Deskew — detect and correct page rotation
    binarized = _deskew(binarized, cv2)

    # Convert back to PIL for Tesseract
    return PILImage.fromarray(binarized)


def _deskew(binary_image, cv2):
    """
    Detect and correct slight page rotation using Hough line transform.
    Handles common scanning artifacts (pages ≤ 15° off axis).

    Args:
        binary_image: Grayscale/binary NumPy image array.
        cv2: OpenCV module.

    Returns:
        Deskewed image as NumPy array.
    """
    try:
        # Find contours/coordinates of non-white pixels
        coords = np.column_stack(np.where(binary_image < 128))
        if len(coords) < 100:
            return binary_image  # Not enough content to detect angle

        # minAreaRect gives the angle of the dominant text orientation
        angle = cv2.minAreaRect(coords)[-1]

        # Normalize angle to [-45, 45]
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90

        # Only correct if rotation is significant (>0.5°) to avoid false corrections
        if abs(angle) < 0.5:
            return binary_image

        logger.debug(f"Deskewing by {angle:.2f}°")
        (h, w) = binary_image.shape
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            binary_image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
    except Exception as e:
        logger.warning(f"Deskew failed (non-critical): {e}")
        return binary_image


def extract_text_from_pdf(pdf_path: str, dpi: int = 300) -> List[Dict]:
    """
    Main entry point: convert each PDF page to an image, preprocess it,
    and run Tesseract OCR to extract text.

    Args:
        pdf_path: Absolute or relative path to the PDF file.
        dpi: Resolution for PDF-to-image conversion. 
             300 DPI is recommended for handwriting — higher = slower but more accurate.

    Returns:
        A list of dicts, one per page:
            [
                {"page": 1, "text": "extracted text..."},
                {"page": 2, "text": "..."},
                ...
            ]
        Returns an empty list if extraction fails.
    """
    convert_from_path, pytesseract, Image, cv2 = _import_dependencies()

    if not Path(pdf_path).is_file():
        logger.error(f"PDF not found: {pdf_path}")
        return []

    logger.info(f"Starting OCR on: {pdf_path} at {dpi} DPI")

    # Tesseract config for handwriting:
    # --oem 1  = LSTM neural net engine (best for cursive/handwriting)
    # --psm 6  = Assume a single uniform block of text
    # -l eng   = English language pack
    tesseract_config = "--oem 1 --psm 6 -l eng"

    try:
        print(f"   Converting PDF to images at {dpi} DPI (this may take a moment)...")
        pdf_images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        logger.error("Make sure poppler is installed: https://poppler.freedesktop.org/")
        return []

    logger.info(f"PDF has {len(pdf_images)} page(s).")
    pages_data = []

    for page_num, pil_image in enumerate(
        tqdm(pdf_images, desc="   OCR pages", unit="page"), start=1
    ):
        try:
            # Preprocess for better OCR accuracy
            processed_image = _preprocess_image_for_ocr(pil_image, cv2)

            # Run Tesseract
            raw_text = pytesseract.image_to_string(processed_image, config=tesseract_config)

            # Basic sanity check — skip blank pages
            clean_text = raw_text.strip()
            if not clean_text:
                logger.warning(f"Page {page_num}: OCR returned empty text (blank/unreadable page).")
                clean_text = ""

            pages_data.append({
                "page": page_num,
                "text": clean_text
            })
            logger.debug(f"Page {page_num}: extracted {len(clean_text)} characters.")

        except Exception as e:
            logger.error(f"OCR failed on page {page_num}: {e}")
            pages_data.append({"page": page_num, "text": ""})

    non_empty = sum(1 for p in pages_data if p["text"])
    logger.info(f"OCR complete: {non_empty}/{len(pages_data)} pages with text.")
    return pages_data
