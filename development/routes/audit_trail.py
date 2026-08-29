# GET /api/audit-trail (view logs)
from flask import Blueprint, jsonify

from models.audit_log import AuditLog


audit_bp = Blueprint(
    "audit",
    __name__,
    url_prefix="/api",
)


@audit_bp.route("/audit-trail", methods=["GET"])
def get_audit_trail():
    """
    Get audit trail entries.

    Used by the coordinator dashboard to review
    assessment, confirmation, override, and
    re-triage events.
    """

    try:
        logs = (
            AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

        audit_data = []

        for log in logs:
            audit_data.append({
                "id": log.id,
                "patient_id": log.patient_id,
                "event_type": log.event_type,
                "timestamp": (
                    log.timestamp.isoformat()
                    if log.timestamp
                    else None
                ),
                "ai_esi": log.ai_esi,
                "ai_confidence": log.ai_confidence,
                "ai_reasoning": log.ai_reasoning,
                "coordinator_esi": log.coordinator_esi,
                "coordinator_reasoning": log.coordinator_reasoning,
                "is_override": log.is_override,
            })

        return jsonify({
            "success": True,
            "audit_logs": audit_data,
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
        }), 500