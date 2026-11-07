"""
Resident Management Module.
Handles registration, administrative updates, biometric template deletion,
and search capabilities for residential society members.
"""

from dataclasses import dataclass
from typing import Optional, Any
import logging
import numpy as np

from database.db import DatabaseManager
from recognition.embeddings import serialize_embedding, deserialize_embedding

logger = logging.getLogger(__name__)

@dataclass
class ResidentRecord:
    """Represents a registered resident."""
    resident_id: str
    full_name: str
    apartment_number: str
    contact_number: Optional[str]
    registration_date: str
    is_active: bool
    consent_given: bool
    notes: Optional[str]
    template_count: int = 0

class ResidentManager:
    """Manages resident lifecycle and biometric template records."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def register_resident(
        self,
        resident_id: str,
        full_name: str,
        apartment_number: str,
        contact_number: Optional[str] = None,
        embeddings: Optional[list[np.ndarray]] = None,
        consent_given: bool = True,
        notes: Optional[str] = None
    ) -> ResidentRecord:
        """
        Enrolls a new resident with informed consent and associated biometric embeddings.
        """
        r_id = resident_id.strip()
        name = full_name.strip()
        apt = apartment_number.strip()

        if not r_id:
            raise ValueError("Resident ID cannot be empty.")
        if not name:
            raise ValueError("Resident Full Name cannot be empty.")
        if not apt:
            raise ValueError("Apartment number cannot be empty.")
        if not consent_given:
            raise ValueError("Informed consent is mandatory for biometric enrollment.")

        # Check for duplicate ID
        existing = self.get_resident(r_id)
        if existing:
            raise ValueError(f"Resident with ID '{r_id}' already exists.")

        # Insert resident record
        insert_resident_sql = """
            INSERT INTO residents (
                resident_id, full_name, apartment_number, contact_number,
                is_active, consent_given, notes
            ) VALUES (?, ?, ?, ?, 1, ?, ?)
        """
        self.db.execute(
            insert_resident_sql,
            (r_id, name, apt, contact_number, 1 if consent_given else 0, notes)
        )

        # Insert enrolled face embeddings if provided
        template_count = 0
        if embeddings:
            insert_emb_sql = """
                INSERT INTO face_embeddings (resident_id, embedding_blob, model_name, sample_tag)
                VALUES (?, ?, 'sface_2021dec', ?)
            """
            for idx, emb in enumerate(embeddings):
                blob = serialize_embedding(emb)
                tag = f"sample_{idx + 1}"
                self.db.execute(insert_emb_sql, (r_id, blob, tag))
                template_count += 1

        logger.info(f"Registered resident '{name}' ({r_id}) with {template_count} template(s).")
        return self.get_resident(r_id)

    def get_resident(self, resident_id: str) -> Optional[ResidentRecord]:
        """Retrieves a single resident record by ID."""
        sql = """
            SELECT 
                r.resident_id, r.full_name, r.apartment_number, r.contact_number,
                r.registration_date, r.is_active, r.consent_given, r.notes,
                COUNT(e.embedding_id) as template_count
            FROM residents r
            LEFT JOIN face_embeddings e ON r.resident_id = e.resident_id
            WHERE r.resident_id = ?
            GROUP BY r.resident_id
        """
        row = self.db.fetch_one(sql, (resident_id,))
        if not row:
            return None
        return ResidentRecord(
            resident_id=row["resident_id"],
            full_name=row["full_name"],
            apartment_number=row["apartment_number"],
            contact_number=row["contact_number"],
            registration_date=str(row["registration_date"]),
            is_active=bool(row["is_active"]),
            consent_given=bool(row["consent_given"]),
            notes=row["notes"],
            template_count=int(row["template_count"])
        )

    def list_residents(
        self,
        search_query: Optional[str] = None,
        active_only: bool = False
    ) -> list[ResidentRecord]:
        """Lists all residents with optional name/apartment search and active filtering."""
        sql = """
            SELECT 
                r.resident_id, r.full_name, r.apartment_number, r.contact_number,
                r.registration_date, r.is_active, r.consent_given, r.notes,
                COUNT(e.embedding_id) as template_count
            FROM residents r
            LEFT JOIN face_embeddings e ON r.resident_id = e.resident_id
            WHERE 1=1
        """
        params = []
        if active_only:
            sql += " AND r.is_active = 1"
        if search_query:
            sql += " AND (r.full_name LIKE ? OR r.resident_id LIKE ? OR r.apartment_number LIKE ?)"
            q = f"%{search_query.strip()}%"
            params.extend([q, q, q])

        sql += " GROUP BY r.resident_id ORDER BY r.registration_date DESC"
        rows = self.db.fetch_all(sql, params)

        return [
            ResidentRecord(
                resident_id=r["resident_id"],
                full_name=r["full_name"],
                apartment_number=r["apartment_number"],
                contact_number=r["contact_number"],
                registration_date=str(r["registration_date"]),
                is_active=bool(r["is_active"]),
                consent_given=bool(r["consent_given"]),
                notes=r["notes"],
                template_count=int(r["template_count"])
            )
            for r in rows
        ]

    def update_resident(
        self,
        resident_id: str,
        full_name: Optional[str] = None,
        apartment_number: Optional[str] = None,
        contact_number: Optional[str] = None,
        is_active: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> Optional[ResidentRecord]:
        """Updates resident profile information."""
        updates = []
        params = []

        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name.strip())
        if apartment_number is not None:
            updates.append("apartment_number = ?")
            params.append(apartment_number.strip())
        if contact_number is not None:
            updates.append("contact_number = ?")
            params.append(contact_number.strip())
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes.strip())

        if not updates:
            return self.get_resident(resident_id)

        params.append(resident_id)
        sql = f"UPDATE residents SET {', '.join(updates)} WHERE resident_id = ?"
        self.db.execute(sql, params)
        logger.info(f"Updated resident {resident_id}")
        return self.get_resident(resident_id)

    def delete_resident(self, resident_id: str) -> bool:
        """
        Permanently deletes a resident.
        Foreign key ON DELETE CASCADE automatically removes all associated biometric templates.
        """
        count = self.db.execute("DELETE FROM residents WHERE resident_id = ?", (resident_id,))
        deleted = (count > 0)
        if deleted:
            logger.info(f"Deleted resident {resident_id} and associated biometric embeddings.")
        return deleted

    def add_embedding(
        self,
        resident_id: str,
        embedding: np.ndarray,
        sample_tag: str = "additional"
    ) -> int:
        """Adds an additional biometric embedding template for a resident."""
        blob = serialize_embedding(embedding)
        sql = """
            INSERT INTO face_embeddings (resident_id, embedding_blob, model_name, sample_tag)
            VALUES (?, ?, 'sface_2021dec', ?)
        """
        emb_id = self.db.execute(sql, (resident_id, blob, sample_tag))
        logger.info(f"Enrolled additional template #{emb_id} for resident {resident_id}")
        return emb_id

    def clear_embeddings(self, resident_id: str) -> int:
        """Deletes all biometric templates for a resident (for re-enrollment)."""
        count = self.db.execute("DELETE FROM face_embeddings WHERE resident_id = ?", (resident_id,))
        logger.info(f"Cleared {count} templates for resident {resident_id}")
        return count

    def get_resident_embeddings(self, resident_id: str) -> list[np.ndarray]:
        """Retrieves all enrolled 128-d biometric vectors for a resident."""
        sql = "SELECT embedding_blob FROM face_embeddings WHERE resident_id = ?"
        rows = self.db.fetch_all(sql, (resident_id,))
        return [deserialize_embedding(r["embedding_blob"]) for r in rows]

