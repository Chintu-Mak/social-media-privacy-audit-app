import io
import base64
import cv2
from io import BytesIO
from PIL import Image
import pytesseract
import exifread
import io
import os
import re
import phonenumbers

import cv2
import numpy as np
import spacy
from .utils import extract_exif, detect_faces_and_blur
import pytesseract
from PIL import Image

from .utils import detect_faces_and_blur, extract_exif

TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

nlp = spacy.load("en_core_web_sm")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
CREDITCARD_RE = re.compile(r"(?:\d[ -]*?){13,16}")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


# ---------- Helper to sanitize numpy types ----------
def to_native(obj):
    """Convert numpy scalars/arrays to Python native types."""
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_native(v) for v in obj]
    return obj


# ---------- OCR & pattern detection ----------
def ocr_image(pil_image):
    # Convert PIL to OpenCV format
    img = np.array(pil_image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply threshold (increase contrast)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # Optional: enlarge image for better OCR
    thresh = cv2.resize(thresh, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    text = pytesseract.image_to_string(thresh)

    print("OCR TEXT:", text)  # Debug line
    return text


PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[ -]?)?(?:\(\d{2,4}\)|\d{2,4})[ -]?)?\d{3,4}[ -]?\d{3,4}")


def find_phones(text):
    phones = []
    for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
        phones.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164))
    return phones
    raw_matches = PHONE_RE.findall(text)
    cleaned = []
    for match in raw_matches:
        digits = re.sub(r"\D", "", match)
        if 10 <= len(digits) <= 15:
            cleaned.append(match.strip())
    return list(dict.fromkeys(cleaned))


def find_emails(text):
    return EMAIL_RE.findall(text)


def find_creditcards(text):
    return CREDITCARD_RE.findall(text)


def find_ssn(text):
    return SSN_RE.findall(text)


def ner_entities(text):
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]
    # Placeholder lightweight entity extraction to avoid hard runtime dependency.
    return []


ADDRESS_KEYWORDS = [
    "street",
    "road",
    "lane",
    "avenue",
    "sector",
    "nagar",
    "colony",
    "apartment",
    "flat",
]

ADDRESS_KEYWORDS = ["street", "road", "lane", "avenue", "sector", "nagar", "colony", "apartment", "flat"]

# ---------- Scoring ----------
def score_report(findings):
    score = 0
    reasons = []
    if findings.get("gps"):
        score += 40
        reasons.append("GPS coordinates found in image metadata")
    if findings.get("faces", 0) > 0:
        score += 15 * findings["faces"]
        reasons.append(f"{findings['faces']} face(s) detected")
    if findings.get("phones"):
        score += 20
        reasons.append("Phone number(s) detected")
    if findings.get("emails"):
        score += 10
        reasons.append("Email address detected")
    if findings.get("creditcards"):
        score += 50
        reasons.append("Possible credit card number found")
    if findings.get("ssn"):
        score += 60
        reasons.append("Possible SSN found")
    if findings.get("sensitive_named_entities"):
        score += 10
        reasons.append("Sensitive named entity (PERSON/ORG/LOC) detected in text")
    if findings.get("addresses"):
        score += 15
        reasons.append("Possible address information detected")
    return min(score, 100), reasons


# ---------- Main analysis ----------
def analyze_image(file_bytes, filename="upload.jpg", caption=None):
    pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    exif = extract_exif(io.BytesIO(file_bytes))
    gps = exif.get("gps")

    # OCR and text-based detection
    ocr_text = ocr_image(pil_img)
    combined_text = f"{caption}\n{ocr_text}" if caption else ocr_text
    emails = find_emails(combined_text)
    phones = find_phones(combined_text)
    creditcards = find_creditcards(combined_text)
    ssn = find_ssn(combined_text)
    ents = ner_entities(combined_text)
    sensitive_ents = [e for e in ents if e[1] in ("PERSON", "ORG", "GPE", "LOC")]
    address_hits = [word for word in ADDRESS_KEYWORDS if word in combined_text.lower()]


    # Face detection
    faces_count, blur_info = detect_faces_and_blur(pil_img)

    # ---------- Create annotated preview ----------
    np_img = np.array(pil_img)
    preview_img = np_img.copy()

    # Draw rectangles for detected faces
    for info in blur_info:
        x, y, w, h = int(info["x"]), int(info["y"]), int(info["w"]), int(info["h"])
        cv2.rectangle(preview_img, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Red box
        cv2.putText(preview_img, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(
            preview_img,
            "Face",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2,
        )

    # If GPS exists, mark as metadata risk
    if gps:
        cv2.putText(preview_img, "⚠ GPS metadata found", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.putText(
            preview_img,
            "GPS metadata found",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            3,
        )

    # Encode preview image as base64
    preview_pil = Image.fromarray(preview_img)
    buffered = io.BytesIO()
    preview_pil.save(buffered, format="JPEG")
    preview_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # ---------- Compile findings ----------
    findings = {
        "filename": filename,
        "gps": gps,
        "ocr_text": ocr_text,
        "emails": emails,
        "phones": phones,
        "creditcards": creditcards,
        "ssn": ssn,
        "entities": ents,
        "sensitive_named_entities": sensitive_ents,
        "addresses": address_hits,
        "faces": faces_count,
        "blur_info": blur_info,
    }

    findings = to_native(findings)
    score, reasons = score_report(findings)
    result = {
        "findings": findings,
        "privacy_risk_score": score,
        "reasons": reasons,
        "recommendations": generate_recommendations(findings, score),
        "preview_image": f"data:image/jpeg;base64,{preview_base64}",
    }
    return result


# ---------- Recommendations ----------
def generate_recommendations(findings, score):
    recs = []
    if findings.get("gps"):
        recs.append("Remove/strip GPS EXIF data before posting or disable location on your camera.")
        recs.append(
            "Remove/strip GPS EXIF data before posting or disable location on your camera."
        )
    if findings.get("faces") and findings["faces"] > 0:
        recs.append("Consider blurring or obscuring faces if people might not want to be identified.")
        recs.append(
            "Consider blurring or obscuring faces if people might not want to be identified."
        )
    if findings.get("phones"):
        recs.append("Remove visible phone numbers from images or redact contact numbers.")
    if findings.get("emails"):
        recs.append("Avoid showing personal email addresses; use contact forms instead.")
    if findings.get("creditcards") or findings.get("ssn"):
        recs.append("DO NOT post sensitive IDs or payment info. Delete or crop sensitive images.")
        recs.append(
            "DO NOT post sensitive IDs or payment info. Delete or crop sensitive images."
        )
    if findings.get("sensitive_named_entities"):
        recs.append("Be cautious with captions or text revealing full names, addresses or employer details.")
        recs.append(
            "Be cautious with captions or text revealing full names, addresses or employer details."
        )
    if score < 20:
        recs.append("Low risk detected — good to go, but double-check before posting.")
    return recs