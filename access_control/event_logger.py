"""
Access Control Audit Logger Module.
Persists entry attempts, tracks security statistics, and supports administrative review.
"""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime
import logging

from database.db import DatabaseManager
from config.settings import DecisionState, VerificationStatus

logger = logging.getLogger(__name__)

@dataclass
class AccessLogRecord:
    """Represents a logged security gate entry attempt."""
    log_id: int
    resident_id: Optional[str]
    detected_name: str
    apartment_number: Optional[str]
    similarity_score: Optional[float]
    decision: DecisionState
    verification_status: VerificationStatus
    timestamp: str
    reason: Optional[str]

class AccessEventLogger:
    """Manages persistent SQLite access log transactions and security audit metrics."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def log_event(
        self,
        decision: DecisionState,
        detected_name: str,
        resident_id: Optional[str] = None,
        apartment_number: Optional[str] = None,
        similarity_score: Optional[float] = None,
        verification_status: VerificationStatus = VerificationStatus.AUTOMATIC,
        reason: Optional[str] = None
    ) -> int:
        """Records an access attempt in the access_logs table."""
        sql = """
            INSERT INTO access_logs (
                resident_id, detected_name, apartment_number, similarity_score,
                decision, verification_status, timestamp, reason
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
        """
        score_val = round(float(similarity_score), 4) if similarity_score is not None else None
        log_id = self.db.execute(
            sql,
            (
                resident_id,
                detected_name,
                apartment_number,
                score_val,
                decision.value,
                verification_status.value,
                reason
            )
        )
        logger.info(
            f"Logged access event #{log_id}: {decision.value} for '{detected_name}' "
            f"(Score: {score_val}, Status: {verification_status.value})"
        )
        return log_id

    def get_recent_logs(self, limit: int = 50) -> list[AccessLogRecord]:
        """Fetches the most recent access logs ordered by timestamp descending."""
        sql = "SELECT * FROM access_logs ORDER BY timestamp DESC, log_id DESC LIMIT ?"
        rows = self.db.fetch_all(sql, (limit,))
        return [self._row_to_record(r) for r in rows]

    def filter_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        decision: Optional[str] = None,
        resident_id: Optional[str] = None,
        limit: int = 200
    ) -> list[AccessLogRecord]:
        """Filters access logs by date range, decision type, or resident ID."""
        sql = "SELECT * FROM access_logs WHERE 1=1"
        params: list[Any] = []

        if start_date:
            sql += " AND date(timestamp) >= date(?)"
            params.append(start_date)
        if end_date:
            sql += " AND date(timestamp) <= date(?)"
            params.append(end_date)
        if decision and decision != "ALL":
            sql += " AND decision = ?"
            params.append(decision)
        if resident_id:
            sql += " AND resident_id = ?"
            params.append(resident_id)

        sql += " ORDER BY timestamp DESC, log_id DESC LIMIT ?"
        params.append(limit)

        rows = self.db.fetch_all(sql, params)
        return [self._row_to_record(r) for r in rows]

    def get_today_statistics(self) -> dict[str, int]:
        """Calculates security gate entry metrics for the current calendar day."""
        sql = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN decision = 'ENTRY ALLOWED' THEN 1 ELSE 0 END) as allowed,
                SUM(CASE WHEN decision = 'ENTRY REJECTED' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN decision = 'VERIFICATION REQUIRED' THEN 1 ELSE 0 END) as verification
            FROM access_logs
            WHERE date(timestamp) = date('now', 'localtime')
        """
        row = self.db.fetch_one(sql)
        if not row or row["total"] is None:
            return {"total": 0, "allowed": 0, "rejected": 0, "verification": 0}

        return {
            "total": int(row["total"] or 0),
            "allowed": int(row["allowed"] or 0),
            "rejected": int(row["rejected"] or 0),
            "verification": int(row["verification"] or 0)
        }

    def update_verification_status(
        self,
        log_id: int,
        new_status: VerificationStatus,
        new_decision: Optional[DecisionState] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Updates review status when security guard executes a manual override."""
        updates = ["verification_status = ?"]
        params: list[Any] = [new_status.value]

        if new_decision:
            updates.append("decision = ?")
            params.append(new_decision.value)
        if notes:
            updates.append("reason = COALESCE(reason, '') || ' | ' || ?")
            params.append(notes)

        params.append(log_id)
        sql = f"UPDATE access_logs SET {', '.join(updates)} WHERE log_id = ?"
        count = self.db.execute(sql, params)
        return count > 0

    @staticmethod
    def _row_to_record(r: dict[str, Any]) -> AccessLogRecord:
        return AccessLogRecord(
            log_id=int(r["log_id"]),
            resident_id=r["resident_id"],
            detected_name=r["detected_name"],
            apartment_number=r["apartment_number"],
            similarity_score=float(r["similarity_score"]) if r["similarity_score"] is not None else None,
            decision=DecisionState(r["decision"]),
            verification_status=VerificationStatus(r["verification_status"]),
            timestamp=str(r["timestamp"]),
            reason=r["reason"]
        )
