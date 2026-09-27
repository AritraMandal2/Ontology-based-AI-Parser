"""
FastAPI Server for GxP Ontology-Triggered Chromatography Platform.
Enforces 21 CFR Part 11 & ALCOA++ Role-Based Access Control (RBAC).
"""

import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from app.agent import (
    extract_and_verify_chromatography_file,
    get_measurement_records,
    approve_quarantined_record,
    get_okg_graph,
    get_gxp_audit_history,
    get_unmapped_residual_tokens,
    seed_sample_vendor_files,
    agent
)
from app.extractor import map_unmapped_residual_token

app = FastAPI(
    title="GxP Chromatography Extraction & Ontology Platform",
    description="21 CFR Part 11 & ALCOA++ Compliant Equipment-Class Ontology Platform",
    version="1.0.0"
)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    seed_sample_vendor_files()

class ExtractionRequest(BaseModel):
    text: str
    filename: Optional[str] = "ad_hoc_sample.txt"

class ApprovalRequest(BaseModel):
    record_id: str
    qa_user: str
    user_role: Optional[str] = "QA_QC"
    comment: str

class ResidualMapRequest(BaseModel):
    token: str
    target_field: str
    user_id: str
    user_role: str
    reason: str

class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>GxP Chromatography Extraction Platform</h1>"


@app.get("/api/records")
def api_get_records(status: Optional[str] = None):
    return get_measurement_records(status)


@app.post("/api/extract")
async def api_extract_file(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    filename: Optional[str] = Form("manual_input.txt")
):
    if file:
        content_bytes = await file.read()
        fname = file.filename or "uploaded_instrument.txt"
        if fname.lower().endswith(".pdf"):
            import io, pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            extracted_pages = [page.extract_text() or "" for page in reader.pages]
            raw_text = "\n".join(extracted_pages)
        else:
            raw_text = content_bytes.decode("utf-8", errors="replace")
    elif text:
        raw_text = text
        fname = filename
    else:
        raise HTTPException(status_code=400, detail="Either file or text must be provided.")

    record = extract_and_verify_chromatography_file(raw_text, fname)
    return record


@app.post("/api/approve")
def api_approve_record(req: ApprovalRequest):
    try:
        updated = approve_quarantined_record(
            req.record_id,
            req.qa_user,
            req.comment,
            req.user_role or "QA_QC"
        )
        return updated
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.post("/api/residuals/map")
def api_map_residual_token(req: ResidualMapRequest):
    try:
        result = map_unmapped_residual_token(
            token=req.token,
            target_ontology_field=req.target_field,
            user_id=req.user_id,
            user_role=req.user_role,
            reason=req.reason
        )
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/graph")
def api_get_graph():
    return get_okg_graph()


@app.get("/api/audit")
def api_get_audit():
    return get_gxp_audit_history()


@app.get("/api/residuals")
def api_get_residuals():
    return get_unmapped_residual_tokens()


@app.post("/api/seed")
def api_seed_data():
    records = seed_sample_vendor_files()
    return {"status": "SUCCESS", "seeded_count": len(records)}


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    records = get_measurement_records()
    audit = get_gxp_audit_history()
    quarantined = [r for r in records if r["verification_status"] == "QUARANTINED"]
    
    reply = f"GxP Audit Trail has {len(audit)} logged events. Active Records: {len(records)} ({len(quarantined)} Quarantined)."
    if "audit" in req.message.lower():
        reply += f" Last capture at {audit[-1]['timestamp'] if audit else 'N/A'}."
    elif "quarantine" in req.message.lower():
        reply += f" Quarantined records require QA/QC Admin role authorization."
    
    return {"response": reply}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8080, reload=True)
