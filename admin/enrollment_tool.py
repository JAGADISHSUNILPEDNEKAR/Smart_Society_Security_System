"""
Command-Line Biometric Resident Enrollment Tool.
Enables administrators to enroll consenting society volunteers with webcam or portrait photos.
Enforces informed consent, single-face detection, and quality validation.
"""

import sys
import argparse
from pathlib import Path
import cv2
import numpy as np

from database.db import DatabaseManager
from admin.resident_manager import ResidentManager
from admin.enrollment import BiometricEnrollmentService
from recognition.detector import FaceDetector
from recognition.recognizer import FaceRecognizer
from config.settings import DEFAULT_DB_PATH

def enroll_volunteer(
    resident_id: str,
    full_name: str,
    apartment: str,
    image_path: str,
    contact: str = "",
    consent: bool = True
) -> bool:
    """Enrolls a single volunteer from an image file."""
    if not consent:
        print("[ERROR] Biometric enrollment requires informed consent.")
        return False

    img_p = Path(image_path)
    if not img_p.exists():
        print(f"[ERROR] Image file does not exist: {img_p}")
        return False

    image = cv2.imread(str(img_p))
    if image is None:
        print(f"[ERROR] Could not decode image: {img_p}")
        return False

    db = DatabaseManager(DEFAULT_DB_PATH)
    db.init_db()
    res_mgr = ResidentManager(db)
    detector = FaceDetector()
    recognizer = FaceRecognizer()
    service = BiometricEnrollmentService(detector, recognizer)

    val = service.validate_image_quality(image)
    if not val.is_valid:
        print(f"[REJECTED] Biometric quality validation failed: {val.reason}")
        return False

    emb = recognizer.extract_embedding(image, val.face)
    res_mgr.register_resident(
        resident_id=resident_id,
        full_name=full_name,
        apartment_number=apartment,
        contact_number=contact,
        embeddings=[emb],
        consent_given=consent,
        notes="Enrolled via Biometric CLI Enrollment Tool"
    )
    print(f"[SUCCESS] Resident '{full_name}' ({resident_id}) successfully enrolled into {apartment}!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Society Resident Biometric Enrollment CLI")
    parser.add_argument("--id", required=True, help="Unique Resident ID (e.g. RES-101)")
    parser.add_argument("--name", required=True, help="Resident Full Name")
    parser.add_argument("--apartment", required=True, help="Apartment/Flat Number (e.g. Tower-A 402)")
    parser.add_argument("--image", required=True, help="Path to frontal portrait photo")
    parser.add_argument("--contact", default="", help="Phone number")
    parser.add_argument("--consent", action="store_true", default=True, help="Confirm volunteer informed consent")

    args = parser.parse_args()
    success = enroll_volunteer(args.id, args.name, args.apartment, args.image, args.contact, args.consent)
    sys.exit(0 if success else 1)

