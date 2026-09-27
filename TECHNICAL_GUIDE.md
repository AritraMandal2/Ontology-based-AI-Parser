# Step-by-Step Technical Guide: GxP Chromatography Extraction & Ontology Agent

This document provides a comprehensive technical walkthrough of the architecture, data pipelines, verification logic, ontology mapping, role-based access controls, knowledge graph generation, and video synthesis tools implemented in the **GxP Chromatography Extraction & Ontology Platform**.

---

## 1. System Overview & Compliance Architecture

The platform provides automated, GxP-compliant telemetry processing for multi-vendor liquid and gas chromatography systems (Agilent, Waters, Shimadzu, Thermo Fisher, PerkinElmer).

```
                      +------------------------------------------+
                      | Raw Multi-Vendor Telemetry File          |
                      | (TXT, CSV, TSV, JSON, PDF Report)        |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      | Ingestion & Cryptographic Provenance     |
                      | - SHA-256 File Hash Generation           |
                      | - 21 CFR Part 11 Digital Signature Hash  |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      | Targeted Ontology Extraction Engine      |
                      | - Vertex AI Gemini 3 Flash Structured    |
                      | - Multi-Vendor Semantic Synonym Fallback |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      | GxP Suitability & Boundary Verification  |
                      | - USP Plate Count (N >= 2000)            |
                      | - Tailing Factor (0.8 <= T <= 2.0)       |
                      | - Precision % RSD (<= 2.0%)              |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      | Status Classification & Quarantining     |
                      | -> PASSED / FLAGGED / QUARANTINED        |
                      +--------------------+---------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
+-------------------+--------------------+   +--------------------+--------------------+
| HITL QA/QC Role-Based Authorization    |   | Knowledge Graph & Visualizer       |
| - Only QA_QC Role Approved (403 for    |   | - Central Hub: ★ Analyte (#F97316) |
|   ANALYST role attempts)               |   | - Cytoscape.js Node/Edge Topology  |
+----------------------------------------+   +-----------------------------------------+
```

---

## 2. Component Deep Dive & Code Walkthrough

### Step 1: Ingestion & Cryptographic Audit Logging (`app/ingestion.py`)

Every file processed by the agent passes through the provenance engine:

1. **SHA-256 Provenance Hash**: `calculate_sha256(content: str)` calculates a deterministic SHA-256 fingerprint for the raw telemetry stream.
2. **21 CFR Part 11 Digital Signature Hash**:
   ```python
   signature_base = f"{user_id}|{user_role}|{event_type}|{file_hash}|{timestamp}|{reason_for_change}"
   digital_signature = hashlib.sha256(signature_base.encode('utf-8')).hexdigest()
   ```
3. **ALCOA++ Metadata Assertion**: Each event records `attributable`, `contemporaneous`, `original_hash`, `accurate`, and `enduring` verification parameters in the `_ALCOA_AUDIT_TRAIL` log array.

---

### Step 2: Targeted Multi-Format Ontology Extraction (`app/extractor.py`)

Extraction executes in two cascading tiers:

#### Primary Tier: Vertex AI Gemini 3 Flash Structured Extraction
Invokes `vertex:gemini-3-flash-preview` in location `us-central1` using temperature `0.0` and enforced JSON schema (`GenerationConfig(response_mime_type="application/json", response_schema=ChromatographyExtraction.model_json_schema())`).

#### Fallback Tier: Multi-Format Semantic Rule Parser (`extract_with_rules_fallback`)
Used if Vertex AI is offline or when parsing raw text files:
- **JSON Parser**: Parses structured JSON payloads directly.
- **CSV / TSV Parser**: Reads tab-delimited and comma-separated header lines, matching headers against the `VENDOR_SYNONYMS` dictionary.
- **Key-Value Pair Parser**: Regex matching on `: = \t ,` delimiters.
- **PDF Extraction**: Reads PDF binary data using `pypdf.PdfReader` and extracts text streams across all pages.
- **Synonym Dictionary (`app/chromatography_ontology.py`)**:
  Maps vendor variations (e.g. `retention time`, `ret. time`, `rt`, `tR`) to canonical ontology target keys (`Retention_Time`).

---

### Step 3: Boundary Reconciliation & Verification (`app/verification.py`)

Extracted telemetry fields are verified against functional GxP suitability limits (`DATA_PACKET_BOUNDS`):

- **Mandatory Fields**: Missing `Sample_ID`, `Retention_Time`, or `Peak_Area` immediately assigns `QUARANTINED` status.
- **USP Theoretical Plate Count ($N$)**: If $N < 2000$, flags `Plate Count below suitability limit (< 2000)`.
- **Tailing Factor ($T$)**: If $T < 0.8$ or $T > 2.0$, flags `Tailing Factor outside ideal range (0.8 - 2.0)`.
- **Precision % RSD**: If $\% \text{RSD} > 2.0\%$, assigns `QUARANTINED` status.

Records are stored in `_MEASUREMENT_RECORDS` with unique identifiers (`REC-<hash_prefix>-<seq>`).

---

### Step 4: Human-in-the-Loop (HITL) Role-Based Access Control

The platform enforces strict 21 CFR Part 11 Access Control (RBAC) across administrative endpoints:

1. **Quarantine Approval (`approve_hitl_quarantine` in `app/verification.py`)**:
   ```python
   if user_role != "QA_QC":
       raise PermissionError("21 CFR Part 11 Access Control Violation: Only QA/QC Admin users can authorize quarantined records.")
   ```
   - Attempting approval with `user_role="ANALYST"` returns **HTTP 403 Forbidden**.
   - Executing approval with `user_role="QA_QC"` updates record status to `REVIEWED_APPROVED` and logs a digital signature audit event.

2. **Residual Token Mapping (`map_unmapped_residual_token` in `app/extractor.py`)**:
   Allows QA/QC Admins to map unmapped file lines directly into `VENDOR_SYNONYMS`, updating the dynamic ontology registry with full audit event traceability.

---

### Step 5: Hierarchical Knowledge Graph (OKG) Engine (`app/measurement_store.py`)

`build_ontology_knowledge_graph()` constructs Cytoscape.js compatible graph structures:

#### Node Hierarchy & Color Coding

| Node Category | Type Key | Color | Description |
|---|---|---|---|
| **Equipment Class** | `equipment_class` | `#3B82F6` (Blue) | Root ontology node: `Equipment Class: Chromatography` |
| **Component Nodes** | `component` | `#06B6D4` / `#F59E0B` / `#10B981` / `#8B5CF6` / `#EC4899` | Hardware components (`Detector`, `Pump`, `Auto-Injector`, `Column`, `Data System`) |
| **Central Analyte Hub** | `analyte_central` | **`#F97316` (Coral Orange)** | Central sample/analyte node (`★ Analyte: <Name>`) linking multi-vendor runs |
| **Molecule Structure** | `molecule` | `#10B981` (Emerald) | Identified chemical structure |
| **Peak Run Nodes** | `peak_run` | `#8B5CF6` (Passed) / `#F59E0B` (Flagged) / `#EF4444` (Quarantined) | Individual chromatographic system runs with retention time $t_R$ and peak parameters |

---

### Step 6: Multimodal Omni 3D Video Generation (`generate_chromatography_item_video` in `app/agent.py`)

The agent registers an async ADK tool for generating 3D item visualization videos:

1. **Model**: Calls `gemini-omni-flash-preview` in location `global` using Vertex AI GenAI SDK client:
   ```python
   client = genai.Client(vertexai=True, project=HARDCODED_PROJECT_ID, location="global")
   ```
2. **Playground Display**: Wraps MP4 bytes in `types.Part(inline_data=types.Blob(mime_type="video/mp4", data=video_bytes))` and invokes `await tool_context.save_artifact(artifact_filename, part)`.
3. **Cloud Storage Upload**: Streams video bytes directly to public GCS bucket `qwiklabs-gcp-02-51c04e7598dd-static-assets-bucket` without writing local disk files, returning `https://storage.googleapis.com/<bucket>/<object_name>.mp4`.

---

## 3. Web API Endpoints & Server (`app/server.py`)

The FastAPI application runs on port `8080`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the interactive web interface (`static/index.html`) |
| `POST` | `/api/seed` | Seeds 15 known molecule chromatography datasets into the store |
| `GET` | `/api/records` | Returns measurement records (optional `status` query filter) |
| `POST` | `/api/extract` | Processes raw text or uploaded PDF files |
| `POST` | `/api/approve` | Approves quarantined records (Enforces `QA_QC` role) |
| `/api/graph` | `GET` | Returns Cytoscape.js OKG nodes and edges |
| `GET` | `/api/residuals` | Lists unmapped residual file tokens |
| `POST` | `/api/residuals/map` | Maps residual tokens to target ontology fields |
| `GET` | `/api/audit` | Returns 21 CFR Part 11 ALCOA+ audit history trail |
| `POST` | `/api/chat` | AI assistant chat interface |

---

## 4. End-to-End Verification Workflow

You can verify all platform capabilities using the included automated verification script:

```bash
uv run python scripts/test_all_features.py
```

### Script Execution Summary

1. Seeds 15 known molecule analytical datasets across 5 vendor systems.
2. Fetches knowledge graph topology and confirms central hub nodes (`★ Analyte`) in coral-orange (`#F97316`).
3. Fetches telemetry records and confirms valid retention times ($t_R > 0.0\text{m}$).
4. Tests raw telemetry parsing for Agilent 1290 format and PDF reports.
5. Verifies 21 CFR Part 11 RBAC access controls (403 for `ANALYST`, 200 for `QA_QC`).
6. Executes HIL residual token mapping and checks digital signature audit entries.
