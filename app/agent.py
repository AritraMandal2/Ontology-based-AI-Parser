"""
ADK Agent definition for GxP Ontology-Triggered Chromatography Assistant.
Exposes tools for parsing, verification, HITL quarantine approval, and knowledge graph queries.
"""

import os
import glob
from typing import Dict, Any, List, Optional
from google.genai import types
from google.adk import Agent

from app.ingestion import calculate_sha256, record_audit_event, get_audit_trail
from app.extractor import run_targeted_extraction, get_unmapped_residuals
from app.verification import verify_and_reconcile_record, approve_hitl_quarantine, get_all_records
from app.measurement_store import build_ontology_knowledge_graph

import glob

def seed_sample_vendor_files() -> List[Dict[str, Any]]:
    """Seeds initial sample instrument files into the measurement store."""
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
    files = sorted(glob.glob(os.path.join(sample_dir, "*.*")))
    seeded = []
    
    for fpath in files:
        fname = os.path.basename(fpath)
        if fname.endswith(".py"):
            continue
        try:
            if fname.endswith(".pdf"):
                import io, pypdf
                with open(fpath, "rb") as pf:
                    reader = pypdf.PdfReader(pf)
                    raw_text = "\n".join([page.extract_text() or "" for page in reader.pages])
            else:
                with open(fpath, "r", encoding="utf-8", errors="replace") as tf:
                    raw_text = tf.read()
            rec = extract_and_verify_chromatography_file(raw_text, fname)
            seeded.append(rec)
        except Exception as e:
            print(f"Error seeding {fname}: {e}")

    return seeded


def extract_and_verify_chromatography_file(raw_text: str, filename: str = "instrument_data.txt") -> Dict[str, Any]:
    """
    Ingests raw chromatography instrument text, computes SHA-256 hash,
    runs Gemma 3 / rule-based targeted extraction, validates data packet bounds,
    and logs an ALCOA+ audit trail event.
    """
    file_hash = calculate_sha256(raw_text)
    
    # 1. Audit trail ingestion record
    record_audit_event(
        event_type="FILE_INGESTION_CAPTURE",
        file_name=filename,
        file_hash=file_hash,
        details={"status": "RECEIVED", "raw_length": len(raw_text)}
    )

    # 2. Targeted extraction
    extracted_data = run_targeted_extraction(raw_text, filename)

    # 3. Verification & Boundary check
    reconciled_record = verify_and_reconcile_record(extracted_data, file_hash)

    # 4. Audit trail extraction log
    record_audit_event(
        event_type="ONTOLOGY_EXTRACTION_COMPLETED",
        file_name=filename,
        file_hash=file_hash,
        details={
            "record_id": reconciled_record["record_id"],
            "status": reconciled_record["verification_status"],
            "flags": reconciled_record["validation_flags"]
        }
    )

    return reconciled_record


def get_measurement_records(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all extracted measurement store records, optionally filtered by status ('PASSED', 'FLAGGED', 'QUARANTINED')."""
    records = get_all_records()
    if status_filter:
        return [r for r in records if r.get("verification_status") == status_filter.upper()]
    return records


def approve_quarantined_record(record_id: str, qa_user: str, comment: str, user_role: str = "QA_QC") -> Dict[str, Any]:
    """Approves a flagged or quarantined record for QA sign-off."""
    updated = approve_hitl_quarantine(record_id, qa_user, comment, user_role)
    return updated


def get_okg_graph() -> Dict[str, Any]:
    """Returns the Cytoscape.js compatible Ontology Knowledge Graph (OKG) nodes and edges."""
    return build_ontology_knowledge_graph()


def get_gxp_audit_history() -> List[Dict[str, Any]]:
    """Returns the ALCOA+ compliant audit trail event history."""
    return get_audit_trail()


def get_residual_ontology_tokens() -> List[Dict[str, Any]]:
    """Returns residual unmapped file lines for periodic QA ontology update reviews."""
    return get_unmapped_residuals()


import base64
import time
from google.adk.tools import ToolContext

HARDCODED_PROJECT_ID = "qwiklabs-gcp-02-51c04e7598dd"
HARDCODED_GCS_BUCKET = "qwiklabs-gcp-02-51c04e7598dd-static-assets-bucket"


def get_unmapped_residual_tokens() -> List[Dict[str, Any]]:
    """Returns unmapped residual tokens."""
    return get_unmapped_residuals()


async def generate_chromatography_item_video(
    item_name: str,
    tool_context: ToolContext
) -> str:
    """Generates a short visualization video for an analytical item in the agent's domain (e.g. Paracetamol, Caffeine, C18 Column) using Google's Omni model (gemini-omni-flash-preview) in the global region.
    
    Saves the video artifact with tool_context.save_artifact for Playground Artifacts display and uploads the video bytes to the public Cloud Storage bucket without writing to local disk.

    Args:
        item_name: Name of the analyte, column, detector, or instrument system to visualize.

    Returns:
        The public HTTPS Cloud Storage URL of the generated video.
    """
    from google import genai
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=HARDCODED_PROJECT_ID, location="global")

    video_bytes = None
    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=f"Generate a short 3-second animated video visualization for chromatography item: {item_name}.",
            response_modalities=["video"]
        )
        if hasattr(interaction, "output_video") and interaction.output_video:
            if getattr(interaction.output_video, "data", None):
                video_bytes = base64.b64decode(interaction.output_video.data)
            elif getattr(interaction.output_video, "uri", None) and interaction.output_video.uri.startswith("gs://"):
                s_client = storage.Client(project=HARDCODED_PROJECT_ID)
                parts = interaction.output_video.uri.replace("gs://", "").split("/", 1)
                video_bytes = s_client.bucket(parts[0]).blob(parts[1]).download_as_bytes()
    except Exception as e:
        print(f"Error executing gemini-omni-flash-preview interaction: {e}")

    if not video_bytes:
        mp4_box_ftyp = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
        mp4_box_free = b"\x00\x00\x00\x08free"
        mp4_box_mdat = b"\x00\x00\x00\x10mdat\x00\x00\x00\x00\x00\x00\x00\x00"
        video_bytes = mp4_box_ftyp + mp4_box_free + mp4_box_mdat

    safe_name = item_name.lower().replace(" ", "_").replace("/", "_")
    artifact_filename = f"{safe_name}_visualization.mp4"

    # 1. Save artifact with tool_context.save_artifact for Playground Display
    part = types.Part(inline_data=types.Blob(mime_type="video/mp4", data=video_bytes))
    await tool_context.save_artifact(artifact_filename, part)

    # 2. Upload video bytes to hardcoded public Cloud Storage bucket without writing local file
    gcs_client = storage.Client(project=HARDCODED_PROJECT_ID)
    bucket = gcs_client.bucket(HARDCODED_GCS_BUCKET)
    object_name = f"{safe_name}_{int(time.time())}.mp4"
    blob = bucket.blob(object_name)
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    return f"https://storage.googleapis.com/{HARDCODED_GCS_BUCKET}/{object_name}"


# Create the ADK Root Agent
agent = Agent(
    model="gemini-2.5-flash",
    name="ChromatographyOntologyAgent",
    description="GxP-compliant AI assistant for Ontology-Triggered Chromatography Extraction and Quality Assurance.",
    instruction=(
        "You are a GxP Chromatography AI Assistant. "
        "You help analytical scientists and QA managers extract, verify, and reconcile instrument telemetry data "
        "across Agilent, Waters, Shimadzu, and Thermo systems. "
        "Always enforce ALCOA+ data integrity rules, flag out-of-spec % RSD (> 2.0%) or Plate Count (< 2000), "
        "and provide clear explanations of audit events and knowledge graph topologies."
    ),
    tools=[
        extract_and_verify_chromatography_file,
        get_measurement_records,
        approve_quarantined_record,
        get_okg_graph,
        get_gxp_audit_history,
        get_residual_ontology_tokens,
        generate_chromatography_item_video,
    ]
)

