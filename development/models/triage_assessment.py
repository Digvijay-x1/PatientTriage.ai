# Assessment result model
from datetime import datetime

from db import db


class TriageAssessment(db.Model):
    __tablename__ = "triage_assessments"

    id = db.Column(db.Integer, primary_key=True)

    # Patient this assessment belongs to
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    # AI recommendation
    ai_esi_level = db.Column(
        db.Integer,
        nullable=False,
    )

    ai_confidence = db.Column(
        db.Float,
        nullable=False,
    )

    confidence_band = db.Column(
        db.String(20),
        nullable=False,
    )

    ai_reasoning = db.Column(
        db.Text,
        nullable=True,
    )

    auto_escalate_for_review = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    # Vital information used during assessment
    vital_details = db.Column(
        db.Text,
        nullable=True,
    )

    # Timestamp
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationship to coordinator decision
    coordinator_decision = db.relationship(
        "CoordinatorDecision",
        backref="assessment",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<TriageAssessment "
            f"id={self.id} "
            f"patient_id={self.patient_id} "
            f"esi={self.ai_esi_level}>"
        )