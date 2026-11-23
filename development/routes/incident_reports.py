# POST /api/incident-reports (report a problem with an AI recommendation)
# GET  /api/incident-reports (provider review queue)
from flask import Blueprint, current_app, jsonify, request

from db import db
from models.incident_report import IncidentReport


incident_bp = Blueprint(
    "incidents",
    __name__,
    url_prefix="/api",
)


@incident_bp.route("/incident-reports", methods=["POST"])
def create_incident_report():
    """
    Record a problem a coordinator found with an AI recommendation.

    A report that says a patient was or may have been harmed is flagged
    as a possible serious incident and raises an alert in the server log,
    so the provider can start the Article 73 procedure in
    docs/compliance/serious-incident-reporting.md.
    """

    data = request.get_json(silent=True) or {}

    description = str(data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "description required"}), 400

    patient_harmed = data.get("patient_harmed") is True

    report = IncidentReport(
        patient_id=data.get("patient_id"),
        assessment_id=data.get("assessment_id"),
        description=description[:4000],
        patient_harmed=patient_harmed,
        possible_serious_incident=patient_harmed,
    )

    try:
        db.session.add(report)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    if report.possible_serious_incident:
        current_app.logger.warning(
            "POSSIBLE SERIOUS INCIDENT: report %s on assessment %s. "
            "Start the serious incident procedure.",
            report.id,
            report.assessment_id,
        )

    return jsonify({
        "success": True,
        "incident_id": report.id,
        "possible_serious_incident": report.possible_serious_incident,
    }), 201


@incident_bp.route("/incident-reports", methods=["GET"])
def list_incident_reports():
    """List reports, possible serious incidents first, newest first."""

    query = IncidentReport.query
    if request.args.get("serious") == "true":
        query = query.filter_by(possible_serious_incident=True)

    reports = query.order_by(
        IncidentReport.possible_serious_incident.desc(),
        IncidentReport.reported_at.desc(),
    ).all()

    return jsonify({
        "success": True,
        "reports": [
            {
                "id": r.id,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
                "patient_id": r.patient_id,
                "assessment_id": r.assessment_id,
                "description": r.description,
                "patient_harmed": r.patient_harmed,
                "possible_serious_incident": r.possible_serious_incident,
                "status": r.status,
            }
            for r in reports
        ],
    }), 200
