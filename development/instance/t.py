import sqlite3

conn = sqlite3.connect("patient_triage.db")
cursor = conn.cursor()

cursor.execute("""
DELETE FROM coordinator_decisions
WHERE assessment_id IN (
    SELECT id
    FROM triage_assessments
    WHERE patient_id IN (7,5,8)
)
""")

cursor.execute("""
DELETE FROM retriage_alerts
WHERE patient_id IN (7,5,8)
""")

cursor.execute("""
DELETE FROM audit_logs
WHERE patient_id IN (7,5,8)
""")

cursor.execute("""
DELETE FROM triage_assessments
WHERE patient_id IN (7,5,8)
""")

cursor.execute("""
DELETE FROM patients
WHERE id IN (7,5,8)
""")

conn.commit()
conn.close()