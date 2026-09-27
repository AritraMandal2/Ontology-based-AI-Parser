"""
Targeted Extraction Engine for Multi-Component Chromatography Ontology.
Supports 21 CFR Part 11 Manual Residual Token Mapping by QA/QC Admin role.
"""

import json
import re
import csv
import io
import os
from typing import Dict, Any, Tuple, List
from app.chromatography_ontology import ChromatographyExtraction, VENDOR_SYNONYMS
from app.ingestion import record_audit_event

_UNMAPPED_RESIDUALS_LOG: List[Dict[str, Any]] = []

SYSTEM_PROMPT = """
You are a GxP-compliant targeted extraction agent for Chromatography result files. 
Your task is to scan the raw instrument file and extract the defined Equipment Class 'Chromatography' schema fields.

HIERARCHICAL COMPONENTS TO POPULATE:
1. 'detector': Common detector fields (System_ID, Manufacturer, Model, Serial_Number, Lab_Location) + Detector specific (UV-VIS, PDA, FLD, RI) fields.
2. 'pump': Pump_Type, Pressure, Flow_Rate, Gradient_Steps, Run_Time, Mobile_Phase_A/B/C/D, Composition, pH, Buffer.
3. 'auto_injector': Injection_ID, Vial_Position, Sample_ID, Injection_Volume, Sequence_ID, Start_Time, Replicate.
4. 'column': Column_ID, Col_Manufacturer, Col_Model, Col_Lot_Number, Col_Stationary_Phase, Col_Length, Col_Temperature, Col_Particle_Size.
5. 'data_system': Sample_ID, Sample_Type, Sample_Name, Matrix, Dilution_Factor, Method_Name, Software, Operator, Retention_Time, Area, Height, Tailing_Factor, Theoretical_Plates, Resolution_To_Prev.

CRITICAL CANONICAL SHORTCUTS:
Map the primary data system values to top-level canonical fields: Sample_ID, Analyte_Name, Equipment_Vendor, Injection_Volume, Retention_Time, Peak_Area, Peak_Height, Tailing_Factor, Plate_Count, Percent_RSD.

EXTRACTION RULES:
1. Extract ONLY the values corresponding to the semantic targets above.
2. Strip all units (e.g. return 1.5, not "1.5 mAU").
3. Base your extraction strictly on the provided text. Zero hallucinations.
"""

def extract_with_rules_fallback(raw_text: str, filename: str = "raw_data.txt") -> Tuple[Dict[str, Any], List[str]]:
    """
    Robust multi-format parser supporting Key-Value, CSV/TSV, and JSON formats.
    Utilizes dynamically updated VENDOR_SYNONYMS ontology mappings.
    """
    extracted = {
        "Equipment_Class": "Chromatography",
        "Sample_ID": "UNKNOWN_SAMPLE",
        "Analyte_Name": "Unknown Compound",
        "Equipment_Vendor": "Generic",
        "Injection_Volume": 10.0,
        "Retention_Time": 0.0,
        "Peak_Area": 0.0,
        "Peak_Height": 0.0,
        "Tailing_Factor": 1.0,
        "Plate_Count": 2500,
        "Percent_RSD": 0.5,
        "detector": {
            "Detector_Type": "UV-VIS",
            "System_ID": "SYS-DET-01",
            "Manufacturer": "Generic",
            "Model": "Standard Detector",
            "Wavelength": 254.0,
            "Temperature": 25.0
        },
        "pump": {
            "Pump_Type": "Binary",
            "Flow_Rate": 1.0,
            "Pressure": 150.0,
            "Mobile_Phase_A": "Water + 0.1% TFA",
            "Mobile_Phase_B": "Acetonitrile"
        },
        "auto_injector": {
            "Vial_Position": "1:A,1",
            "Injection_Volume": 10.0,
            "Replicate": 1
        },
        "column": {
            "Col_Model": "C18 Reverse Phase",
            "Col_Length": 150.0,
            "Col_Temperature": 30.0,
            "Col_Particle_Size": 3.5
        },
        "data_system": {
            "Acquisition_Software": "CDS Platform",
            "Software_Version": "1.0",
            "Operator": "GxP_Analyst"
        }
    }

    # Attempt JSON
    raw_clean = raw_text.strip()
    if raw_clean.startswith("{") and raw_clean.endswith("}"):
        try:
            json_parsed = json.loads(raw_clean)
            if isinstance(json_parsed, dict):
                for k, v in json_parsed.items():
                    if k in extracted and isinstance(v, dict):
                        extracted[k].update(v)
                    else:
                        extracted[k] = v
                return extracted, []
        except Exception:
            pass

    text_lower = raw_text.lower()
    if "shimadzu" in text_lower or "labsolutions" in text_lower:
        extracted["Equipment_Vendor"] = "Shimadzu"
        extracted["detector"]["Manufacturer"] = "Shimadzu"
        extracted["data_system"]["Acquisition_Software"] = "LabSolutions"
    elif "waters" in text_lower or "empower" in text_lower:
        extracted["Equipment_Vendor"] = "Waters"
        extracted["detector"]["Manufacturer"] = "Waters"
        extracted["data_system"]["Acquisition_Software"] = "Empower 3"
    elif "chromeleon" in text_lower or "thermo" in text_lower:
        extracted["Equipment_Vendor"] = "Thermo"
        extracted["detector"]["Manufacturer"] = "Thermo Fisher"
        extracted["data_system"]["Acquisition_Software"] = "Chromeleon"
    elif "agilent" in text_lower or "openlab" in text_lower:
        extracted["Equipment_Vendor"] = "Agilent"
        extracted["detector"]["Manufacturer"] = "Agilent"
        extracted["data_system"]["Acquisition_Software"] = "OpenLab CDS"

    if "pda" in text_lower or "diode array" in text_lower:
        extracted["detector"]["Detector_Type"] = "PDA"
        extracted["detector"]["Number_of_Diodes"] = 512
        extracted["detector"]["Spectral_Range"] = "190-800 nm"
    elif "fld" in text_lower or "fluorescence" in text_lower:
        extracted["detector"]["Detector_Type"] = "FLD"
        extracted["detector"]["Excitation_Wavelength"] = 280.0
        extracted["detector"]["Emission_Wavelength"] = "340 nm"
    elif "ri" in text_lower or "refractive index" in text_lower:
        extracted["detector"]["Detector_Type"] = "RI"
        extracted["detector"]["Cell_Temperature"] = 35.0

    unmapped_lines = []
    lines = raw_clean.splitlines()

    # CSV / TSV Tabular Check
    if ("," in raw_text or "\t" in raw_text) and len(lines) >= 2:
        try:
            delimiter = "\t" if "\t" in lines[0] else ","
            reader = list(csv.reader(io.StringIO(raw_text), delimiter=delimiter))
            if len(reader) >= 2 and len(reader[0]) >= 2:
                header = [h.strip() for h in reader[0]]
                header_map = {}
                for idx, h_text in enumerate(header):
                    h_lower = h_text.lower()
                    for field, synonyms in VENDOR_SYNONYMS.items():
                        for syn in synonyms:
                            if h_lower == syn.lower() or syn.lower() in h_lower or h_lower in syn.lower():
                                header_map[idx] = field
                                break
                        if idx in header_map:
                            break

                if header_map and len(reader) > 1:
                    data_row = reader[1]
                    for idx, field in header_map.items():
                        if idx < len(data_row):
                            val = data_row[idx].strip()
                            if field == "Sample_ID":
                                extracted["Sample_ID"] = val
                                extracted["auto_injector"]["Sample_ID"] = val
                                extracted["data_system"]["Sample_ID"] = val
                            elif field == "Analyte_Name":
                                extracted["Analyte_Name"] = val
                                extracted["data_system"]["Analyte_ID"] = val
                            elif field in ["Injection_Volume", "Retention_Time", "Peak_Area", "Peak_Height", "Tailing_Factor", "Percent_RSD"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match:
                                    num_val = float(num_match.group())
                                    extracted[field] = num_val
                                    if field == "Injection_Volume":
                                        extracted["auto_injector"]["Injection_Volume"] = num_val
                                    elif field == "Retention_Time":
                                        extracted["data_system"]["Retention_Time"] = num_val
                                    elif field == "Peak_Area":
                                        extracted["data_system"]["Area"] = num_val
                                    elif field == "Peak_Height":
                                        extracted["data_system"]["Height"] = num_val
                                    elif field == "Tailing_Factor":
                                        extracted["data_system"]["Tailing_Factor"] = num_val
                            elif field == "Plate_Count":
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match:
                                    int_val = int(float(num_match.group()))
                                    extracted["Plate_Count"] = int_val
                                    extracted["data_system"]["Theoretical_Plates"] = int_val
                            elif field in ["Col_Manufacturer", "Col_Model", "Col_Length", "Col_Temperature", "Col_Particle_Size", "Col_Lot_Number"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match and field in ["Col_Length", "Col_Temperature", "Col_Particle_Size"]:
                                    extracted["column"][field] = float(num_match.group())
                                else:
                                    extracted["column"][field] = val
        except Exception:
            pass

    # Key-Value Parser
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#") or line_clean.startswith("//"):
            continue

        matched = False
        
        if ":" in line_clean or "=" in line_clean or "\t" in line_clean or "," in line_clean:
            parts = re.split(r'[:=\t,]', line_clean, maxsplit=1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()

                for field, synonyms in VENDOR_SYNONYMS.items():
                    for syn in synonyms:
                        if key.lower() == syn.lower() or syn.lower() in key.lower() or key.lower() in syn.lower():
                            matched = True
                            
                            if field == "Sample_ID":
                                extracted["Sample_ID"] = val
                                extracted["auto_injector"]["Sample_ID"] = val
                                extracted["data_system"]["Sample_ID"] = val
                            elif field == "Analyte_Name":
                                extracted["Analyte_Name"] = val
                                extracted["data_system"]["Analyte_ID"] = val
                            elif field in ["Injection_Volume", "Retention_Time", "Peak_Area", "Peak_Height", "Tailing_Factor", "Percent_RSD"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match:
                                    num_val = float(num_match.group())
                                    extracted[field] = num_val
                                    if field == "Injection_Volume":
                                        extracted["auto_injector"]["Injection_Volume"] = num_val
                                    elif field == "Retention_Time":
                                        extracted["data_system"]["Retention_Time"] = num_val
                                    elif field == "Peak_Area":
                                        extracted["data_system"]["Area"] = num_val
                                    elif field == "Peak_Height":
                                        extracted["data_system"]["Height"] = num_val
                                    elif field == "Tailing_Factor":
                                        extracted["data_system"]["Tailing_Factor"] = num_val
                            elif field == "Plate_Count":
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match:
                                    int_val = int(float(num_match.group()))
                                    extracted["Plate_Count"] = int_val
                                    extracted["data_system"]["Theoretical_Plates"] = int_val
                            elif field in ["Wavelength", "Reference_Wavelength", "Bandwidth", "Path_Length", "Temperature", "Lamp_Type", "Lamp_Hours", "Detector_Type"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match and field not in ["Lamp_Type", "Detector_Type"]:
                                    extracted["detector"][field] = float(num_match.group())
                                else:
                                    extracted["detector"][field] = val
                            elif field in ["Flow_Rate", "Pressure", "Pump_Type", "Mobile_Phase_A", "Mobile_Phase_B", "pH"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match and field in ["Flow_Rate", "Pressure"]:
                                    extracted["pump"][field] = float(num_match.group())
                                else:
                                    extracted["pump"][field] = val
                            elif field in ["Col_Manufacturer", "Col_Model", "Col_Length", "Col_Temperature", "Col_Particle_Size", "Col_Lot_Number"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match and field in ["Col_Length", "Col_Temperature", "Col_Particle_Size"]:
                                    extracted["column"][field] = float(num_match.group())
                                else:
                                    extracted["column"][field] = val
                            elif field in ["Operator", "Sample_Type", "Matrix", "Resolution_To_Prev"]:
                                num_match = re.search(r'[-+]?\d*\.?\d+', val)
                                if num_match and field == "Resolution_To_Prev":
                                    extracted["data_system"][field] = float(num_match.group())
                                else:
                                    extracted["data_system"][field] = val
                            break
                    if matched:
                        break

        if not matched:
            unmapped_lines.append(line_clean)

    # RegEx Fallback pass for Retention Time, Wavelength, and Column info
    if extracted["Retention_Time"] == 0.0:
        rt_match = re.search(r'(?:retention\s*time|ret\.?\s*time|rt)[^\d\n]*[:=\t, ]\s*([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if rt_match:
            try:
                extracted["Retention_Time"] = float(rt_match.group(1))
                extracted["data_system"]["Retention_Time"] = float(rt_match.group(1))
            except ValueError:
                pass

    if extracted["detector"].get("Wavelength") == 254.0:
        wl_match = re.search(r'(?:wavelength|wl)[^\d\n]*[:=\t, ]\s*([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if wl_match:
            try:
                extracted["detector"]["Wavelength"] = float(wl_match.group(1))
            except ValueError:
                pass

    col_match = re.search(r'(?:column|col\s*model|col\s*spec)[^\n:=]*[:=]\s*([^\n]+)', raw_text, re.IGNORECASE)
    if col_match:
        extracted["column"]["Col_Model"] = col_match.group(1).strip()

    if unmapped_lines:
        _UNMAPPED_RESIDUALS_LOG.append({
            "filename": filename,
            "vendor": extracted["Equipment_Vendor"],
            "unmapped_lines": unmapped_lines
        })

    return extracted, unmapped_lines


def run_targeted_extraction(raw_text: str, filename: str = "raw_data.txt") -> Dict[str, Any]:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-51c04e7598dd")

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, GenerationConfig

        vertexai.init(project=project_id, location="us-central1")
        
        model = GenerativeModel("vertex:gemini-3-flash-preview", system_instruction=SYSTEM_PROMPT)
        config = GenerationConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ChromatographyExtraction.model_json_schema()
        )
        
        user_prompt = f"Extract canonical multi-component chromatography fields from raw instrument file ({filename}):\n\n{raw_text}"
        response = model.generate_content(user_prompt, generation_config=config)
        
        extracted_data = json.loads(response.text)
        extracted_data["Extraction_Method"] = "Vertex_AI_Gemma3_StructuredJSON"
        return extracted_data

    except Exception as e:
        extracted_data, unmapped = extract_with_rules_fallback(raw_text, filename)
        extracted_data["Extraction_Method"] = "Local_Semantic_RuleParser_Fallback"
        extracted_data["Unmapped_Token_Count"] = len(unmapped)
        return extracted_data


def get_unmapped_residuals() -> List[Dict[str, Any]]:
    return list(_UNMAPPED_RESIDUALS_LOG)


def map_unmapped_residual_token(
    token: str,
    target_ontology_field: str,
    user_id: str,
    user_role: str,
    reason: str
) -> Dict[str, Any]:
    """
    21 CFR Part 11 & ALCOA++ HITL Manual Residual Mapping Endpoint.
    Strictly enforced: Only QA_QC role can perform manual mapping.
    """
    if user_role != "QA_QC":
        raise PermissionError("21 CFR Part 11 Access Control Violation: Only QA/QC Admin users can manually map unmapped residual tokens.")

    if target_ontology_field not in VENDOR_SYNONYMS:
        VENDOR_SYNONYMS[target_ontology_field] = []

    if token not in VENDOR_SYNONYMS[target_ontology_field]:
        VENDOR_SYNONYMS[target_ontology_field].append(token)

    # Clean from unmapped residuals log
    for entry in _UNMAPPED_RESIDUALS_LOG:
        if token in entry.get("unmapped_lines", []):
            entry["unmapped_lines"].remove(token)

    # Log 21 CFR Part 11 Audit Event with digital signature
    audit_event = record_audit_event(
        event_type="HITL_RESIDUAL_TOKEN_ONTOLOGY_MAPPING",
        file_name="Dynamic_Ontology_Registry",
        file_hash="SYNONYM_TABLE_MUTATION",
        user_id=user_id,
        user_role=user_role,
        reason_for_change=reason,
        details={
            "token": token,
            "mapped_to_field": target_ontology_field
        },
        pre_state={"token_status": "UNMAPPED"},
        post_state={"token_status": "MAPPED", "ontology_target": target_ontology_field}
    )

    return {
        "status": "SUCCESS",
        "token": token,
        "mapped_to": target_ontology_field,
        "audit_event": audit_event
    }
