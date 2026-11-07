"""
Demo Resident Database Seeder for Smart Society Security System.
Populates the SQLite database with 20 sample consenting resident records
across Tower A, Tower B, and Tower C with normalized biometric feature embeddings.
"""

import sys
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DEFAULT_DB_PATH
from database.db import DatabaseManager
from admin.resident_manager import ResidentManager

SAMPLE_RESIDENTS = [
    ("RES-101", "Aarav Patel", "Tower-A 101", "+91-9876543201", "Owner, 3BHK"),
    ("RES-102", "Priya Sharma", "Tower-A 102", "+91-9876543202", "Tenant, Agreement valid 2027"),
    ("RES-103", "Rohan Mehta", "Tower-A 201", "+91-9876543203", "Owner, Committee Member"),
    ("RES-104", "Ananya Iyer", "Tower-A 202", "+91-9876543204", "Owner, 2BHK"),
    ("RES-105", "Vikram Singh", "Tower-A 301", "+91-9876543205", "Owner, 3BHK"),
    ("RES-106", "Neha Kulkarni", "Tower-A 302", "+91-9876543206", "Tenant"),
    ("RES-107", "Kabir Sen", "Tower-A 401", "+91-9876543207", "Owner, Penthouse"),
    ("RES-108", "Ishita Nair", "Tower-B 101", "+91-9876543208", "Owner, 2BHK"),
    ("RES-109", "Arjun Reddy", "Tower-B 102", "+91-9876543209", "Owner, Secretary"),
    ("RES-110", "Sneha Joshi", "Tower-B 201", "+91-9876543210", "Tenant, Agreement valid 2028"),
    ("RES-111", "Aditya Verma", "Tower-B 202", "+91-9876543211", "Owner, 3BHK"),
    ("RES-112", "Kavya Menon", "Tower-B 301", "+91-9876543212", "Owner, 2BHK"),
    ("RES-113", "Siddharth Rao", "Tower-B 302", "+91-9876543213", "Tenant"),
    ("RES-114", "Pooja Deshmukh", "Tower-C 101", "+91-9876543214", "Owner, Treasurer"),
    ("RES-115", "Gaurav Malhotra", "Tower-C 102", "+91-9876543215", "Owner, 3BHK"),
    ("RES-116", "Ritu Banerjee", "Tower-C 201", "+91-9876543216", "Tenant, Agreement valid 2027"),
    ("RES-117", "Manish Saxena", "Tower-C 202", "+91-9876543217", "Owner, 2BHK"),
    ("RES-118", "Deepika Pillai", "Tower-C 301", "+91-9876543218", "Owner, 3BHK"),
    ("RES-119", "Karan Kapoor", "Tower-C 302", "+91-9876543219", "Tenant"),
    ("RES-120", "Meera Nambiar", "Tower-C 401", "+91-9876543220", "Owner, Penthouse")
]

def seed_demo_residents(db_path=DEFAULT_DB_PATH, overwrite=False):
    db = DatabaseManager(db_path)
    db.init_db()
    mgr = ResidentManager(db)

    print(f"Seeding demo resident cohort into: {db_path}...")
    rng = np.random.default_rng(2026)

    enrolled = 0
    for r_id, name, apt, phone, notes in SAMPLE_RESIDENTS:
        existing = mgr.get_resident(r_id)
        if existing and not overwrite:
            continue

        if existing and overwrite:
            mgr.delete_resident(r_id)

        # Synthesize 3 multi-sample feature templates (frontal, tilt-left, tilt-right)
        base_center = rng.standard_normal(128).astype(np.float32)
        base_center = base_center / np.linalg.norm(base_center)

        samples = []
        for _ in range(3):
            noise = rng.normal(0.0, 0.06, 128).astype(np.float32)
            s = base_center + noise
            samples.append(s / np.linalg.norm(s))

        mgr.register_resident(
            resident_id=r_id,
            full_name=name,
            apartment_number=apt,
            contact_number=phone,
            embeddings=samples,
            consent_given=True,
            notes=notes
        )
        enrolled += 1

    total = len(mgr.list_residents())
    print(f"[SUCCESS] Seeded {enrolled} new resident records. Total in database: {total}")
    return total

if __name__ == "__main__":
    overwrite = "--overwrite" in sys.argv
    seed_demo_residents(overwrite=overwrite)
