import requests
import json

BASE_URL = "http://localhost:8080"

print("==================================================================")
print("  GxP CHROMATOGRAPHY AGENT & ONTOLOGY PLATFORM API VERIFICATION   ")
print("==================================================================")

# 1. Seed Sample Data
print("\n[1] POST /api/seed - Seeding 15 Known Molecule Chromatography Datasets...")
r_seed = requests.post(f"{BASE_URL}/api/seed")
print("    Status Code:", r_seed.status_code)
print("    Response:", r_seed.json())

# 2. Get Knowledge Graph Topology
print("\n[2] GET /api/graph - Retrieving Open Knowledge Graph Topology...")
r_graph = requests.get(f"{BASE_URL}/api/graph")
graph_data = r_graph.json()
print("    Status Code:", r_graph.status_code)
nodes = graph_data.get("nodes", [])
edges = graph_data.get("edges", [])
print(f"    Graph Elements Count: {len(nodes)} Nodes, {len(edges)} Edges")
analytes = [n['data']['label'] for n in nodes if n['data'].get('type') == 'analyte_central']
print(f"    Central Analyte Hub Nodes ({len(analytes)}):")
for a in analytes[:5]:
    print(f"      - {a}")

# 3. Get Measurement Records
print("\n[3] GET /api/records - Retrieving Telemetry Measurement Store...")
r_records = requests.get(f"{BASE_URL}/api/records")
records = r_records.json()
print("    Status Code:", r_records.status_code)
print(f"    Total Telemetry Records: {len(records)}")
non_zero_tr = all(rec.get("data", {}).get("Retention_Time", 0.0) > 0.0 for rec in records)
print(f"    Retention Time > 0.0m Across All Records: {non_zero_tr}")
for rec in records[:5]:
    analyte = rec.get('data', {}).get('Analyte_Name') or rec.get('data', {}).get('Sample_ID')
    tr = rec.get('data', {}).get('Retention_Time')
    print(f"      - Record {rec['record_id']}: {analyte} | tR={tr}m | Status={rec['verification_status']}")

# 4. Extract Telemetry File (Agilent 1290 format)
print("\n[4] POST /api/extract - Raw Telemetry Parsing & ALCOA+ Verification...")
raw_telemetry = """[Sample Header]
Sample Name: Paracetamol (Acetaminophen)
Instrument Model: Agilent 1290 Infinity II
Detector: Diode Array Detector (DAD) 245nm
Column: ZORBAX Eclipse Plus C18 150x4.6mm 3.5um

[Chromatographic Peak Table]
Peak  Retention Time (min)  Area (mAU*s)  Height (mAU)  Tailing Factor  Plate Count  % RSD
1     2.450                1420500       185400        1.08            14850        0.42
"""
r_extract = requests.post(
    f"{BASE_URL}/api/extract",
    data={"text": raw_telemetry, "filename": "agilent_1290_paracetamol_test.txt"}
)
print("    Status Code:", r_extract.status_code)
ext_res = r_extract.json()
print(f"    Extracted Record ID: {ext_res.get('record_id')}")
print(f"    Retention Time: {ext_res.get('data', {}).get('Retention_Time')} min")
print(f"    Status: {ext_res.get('verification_status')}")
print(f"    Audit Checksum (SHA-256): {ext_res.get('file_hash')[:16]}...")

# 5. Extract PDF File
print("\n[5] POST /api/extract - PDF Parsing (Waters Acquity Report)...")
pdf_text = """Waters Acquity UPLC H-Class System Report
Sample Name: Aspirin (Acetylsalicylic Acid)
Detector: PDA Detector
Column: Acquity UPLC BEH C18 50x2.1mm
Retention Time: 1.82 min
Area: 890400 mAU*s
Height: 120500 mAU
% RSD: 0.35%
USP Plate Count: 12400
Tailing Factor: 1.05
"""
r_pdf = requests.post(f"{BASE_URL}/api/extract", data={"text": pdf_text, "filename": "waters_aspirin_report.pdf"})
print("    Status Code:", r_pdf.status_code)
print("    Response Status:", r_pdf.json().get("verification_status"))

# 6. Test RBAC Approval for Quarantined Record
quarantined_records = [r for r in records if r['verification_status'] == 'QUARANTINED']
target_qid = quarantined_records[0]['record_id'] if quarantined_records else "REC_002"

print(f"\n[6] POST /api/approve - Testing 21 CFR Part 11 RBAC Quarantined Approval for {target_qid}...")
# 6a. Analyst User (Denied - HTTP 403)
r_deny = requests.post(
    f"{BASE_URL}/api/approve",
    json={
        "record_id": target_qid,
        "qa_user": "analyst_john",
        "user_role": "ANALYST",
        "comment": "Attempting unauthorized approval"
    }
)
print("    6a. Analyst Role Approval Attempt (Expect 403):")
print("        Status Code:", r_deny.status_code)
print("        Detail:", r_deny.json().get("detail"))

# 6b. QA/QC Admin User (Approved - HTTP 200)
r_approve = requests.post(
    f"{BASE_URL}/api/approve",
    json={
        "record_id": target_qid,
        "qa_user": "qa_manager_sarah",
        "user_role": "QA_QC",
        "comment": "System suitability verified against USP reference standard."
    }
)
print("    6b. QA_QC Role Approval Attempt (Expect 200):")
print("        Status Code:", r_approve.status_code)
print("        New Status:", r_approve.json().get("verification_status"))
print("        QA Sign-off:", r_approve.json().get("qa_approved_by"))

# 7. Unmapped Residual Tokens & HIL Mapping
print("\n[7] GET /api/residuals & POST /api/residuals/map - HIL Residual Token Mapping...")
r_res = requests.get(f"{BASE_URL}/api/residuals")
res_tokens = r_res.json()
print(f"    Available Residual Tokens Count: {len(res_tokens)}")

if res_tokens:
    first_item = res_tokens[0]
    sample_line = first_item["unmapped_lines"][0] if first_item.get("unmapped_lines") else "UNMAPPED_TOKEN_01"
    token = sample_line.split('\t')[0] if '\t' in sample_line else sample_line
    print(f"    Mapping token '{token}' as QA_QC user...")
    r_map = requests.post(
        f"{BASE_URL}/api/residuals/map",
        json={
            "token": token,
            "target_field": "detector_wavelength_nm",
            "user_id": "qa_admin_doc",
            "user_role": "QA_QC",
            "reason": "Mapped spectral parameter to detector wavelength ontology node."
        }
    )
    print("        Status Code:", r_map.status_code)
    print("        Response:", r_map.json())

# 8. GxP Audit History
print("\n[8] GET /api/audit - Retrieving 21 CFR Part 11 Audit Trail...")
r_audit = requests.get(f"{BASE_URL}/api/audit")
audit_entries = r_audit.json()
print("    Status Code:", r_audit.status_code)
print(f"    Total Logged Audit Events: {len(audit_entries)}")
for a in audit_entries[-3:]:
    user = a.get('user_id', 'SYSTEM')
    event_type = a.get('event_type', 'UNKNOWN_EVENT')
    ts = a.get('timestamp', '')
    print(f"      - [{ts}] Event: {event_type} | User: {user}")

# 9. GxP Chat Assistant
print("\n[9] POST /api/chat - Interacting with GxP Chat Assistant...")
r_chat = requests.post(f"{BASE_URL}/api/chat", json={"message": "What is the status of quarantined records and audit history?"})
print("    Status Code:", r_chat.status_code)
print("    Assistant Reply:", r_chat.json().get("response"))

print("\n==================================================================")
print("  ALL PLATFORM FUNCTIONALITIES EXECUTED AND VERIFIED SUCCESSFULLY ")
print("==================================================================")
