# Problem reports on AI recommendations
from datetime import datetime
from db import db


class IncidentReport(db.Model):
    """
    A problem with an AI recommendation, reported by a coordinator.

    possible_serious_incident is set when the reporter says a patient was
    or may have been harmed. The provider's quality and regulatory lead
    reviews those first, under docs/compliance/serious-incident-reporting.md.
    """
    __tablename__ = 'incident_reports'

    id = db.Column(db.Integer, primary_key=True)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('triage_assessments.id'), nullable=True)

    description = db.Column(db.Text, nullable=False)
    patient_harmed = db.Column(db.Boolean, default=False, nullable=False)
    possible_serious_incident = db.Column(db.Boolean, default=False, nullable=False)

    # open, under_review, reported_to_authority, closed
    status = db.Column(db.String(30), default='open', nullable=False)

    def __repr__(self):
        return f'<IncidentReport {self.id} serious={self.possible_serious_incident}>'
