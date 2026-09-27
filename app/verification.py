"""
Verification, Boundary Reconciliation & Human-In-The-Loop (HITL) Quarantine Engine.
Enforces 21 CFR Part 11 & ALCOA++ compliance rules.
"""

from typing import Dict, Any, List, Tuple
from app.chromatography_ontology import DATA_PACKET_BOUNDS
from app.ingestion import record_audit_event

_MEASUREMENT_RECORDS: List[Dict[str, Any]] = []

def verify_and_reconcile_record(record: Dict[str, Any], file_hash: str) -> Dict[str, Any]:
    """
    Evaluates extracted data fields against functional Data Packet bounds.
    Flags or Quarantines records failing GxP boundary/completeness assertions.
    """
    flags: List[str] = []
    status = "PASSED"

    mandatory_fields = ["Sample_ID", "Retention_Time", "Peak_Area"]
    for field in mandatory_fields:
        if not record.get(field):
            flags.append(f"Missing mandatory field: {field}")
            status = "QUARANTINED"

    plate_count = record.get("Plate_Count", 0)
    if plate_count < DATA_PACKET_BOUNDS["Plate_Count"]["min_suitability"]:
        flags.append(f"Plate Count (N={plate_count}) below suitability limit (< 2000)")
        if status != "QUARANTINED":
            status = "FLAGGED"

    tailing = record.get("Tailing_Factor", 1.0)
    if tailing < DATA_PACKET_BOUNDS["Tailing_Factor"]["min_ideal"] or tailing > DATA_PACKET_BOUNDS["Tailing_Factor"]["max_ideal"]:
        flags.append(f"Tailing Factor ({tailing}) outside ideal range (0.8 - 2.0)")
        if status != "QUARANTINED":
            status = "FLAGGED"

    rsd = record.get("Percent_RSD", 0.0)
    if rsd is not None and rsd > DATA_PACKET_BOUNDS["Percent_RSD"]["max_allowed"]:
        flags.append(f"Precision % RSD ({rsd}%) exceeds maximum threshold (> 2.0%)")
        status = "QUARANTINED"

    validated_record = {
        "record_id": f"REC-{file_hash[:8]}-{len(_MEASUREMENT_RECORDS)+1:03d}",
        "file_hash": file_hash,
        "data": record,
        "verification_status": status,
        "validation_flags": flags,
        "qa_approval": {
            "approved": status == "PASSED",
            "approver": "Automated_Engine" if status == "PASSED" else None,
            "comment": "System boundary check passed" if status == "PASSED" else "Awaiting QA HITL Review"
        }
    }

    _MEASUREMENT_RECORDS.append(validated_record)
    return validated_record

def approve_hitl_quarantine(
    record_id: str,
    qa_user: str,
    qa_comment: str,
    user_role: str = "QA_QC"
) -> Dict[str, Any]:
    """
    21 CFR Part 11 & ALCOA++ HITL Quarantine Approval.
    Strictly enforced: Only QA_QC Admin role can perform overrides.
    """
    if user_role != "QA_QC":
        raise PermissionError("21 CFR Part 11 Access Control Violation: Only QA/QC Admin users can authorize quarantined records.")

    for rec in _MEASUREMENT_RECORDS:
        if rec["record_id"] == record_id:
            pre_status = rec["verification_status"]
            rec["verification_status"] = "REVIEWED_APPROVED"
            rec["qa_approval"] = {
                "approved": True,
                "approver": qa_user,
                "comment": qa_comment,
                "role": user_role
            }

            # 21 CFR Part 11 Audit Event with digital signature
            record_audit_event(
                event_type="HITL_QA_QUARANTINE_OVERRIDE",
                file_name=f"Record_{record_id}",
                file_hash=rec.get("file_hash", "RECORD_OVERRIDE"),
                user_id=qa_user,
                user_role=user_role,
                reason_for_change=qa_comment,
                pre_state={"verification_status": pre_status},
                post_state={"verification_status": "REVIEWED_APPROVED", "qa_approval": rec["qa_approval"]}
            )
            return rec

    raise ValueError(f"Record {record_id} not found in measurement store.")

def get_all_records() -> List[Dict[str, Any]]:
    """Returns all measurement records."""
    return list(_MEASUREMENT_RECORDS)
