"""
Measurement Store & Hierarchical Ontology Knowledge Graph (OKG) Builder.
Generates connected Cytoscape.js nodes and edges linking:
Equipment Class: Chromatography
  ├── Component: Detector (UV-Vis, PDA, FLD, RI) -> Wavelength, Temp, Diodes
  ├── Component: Pump -> Flow Rate, Pressure, Mobile Phases
  ├── Component: Auto-Injector -> Vial Position, Injection Vol, Start Time
  ├── Component: Column -> Model, Stationary Phase, Temp, Length
  └── Component: Data System
       ├── Sample (Sample ID, Name, Type, Matrix)
       ├── Method (Method Name, Version, Software, Operator)
       ├── Peak Chromatogram Run (Retention Time, Area, Height, Tailing, Plates, % RSD, Status)
       └── Molecule / Analyte
"""

from typing import Dict, Any, List
from app.verification import get_all_records

def build_ontology_knowledge_graph() -> Dict[str, Any]:
    records = get_all_records()
    nodes = []
    edges = []
    
    seen_nodes = set()

    # 1. Root Equipment Class Node
    equipment_class_id = "class_chromatography"
    nodes.append({
        "data": {
            "id": equipment_class_id,
            "label": "Equipment Class: Chromatography",
            "type": "equipment_class",
            "color": "#3B82F6"
        }
    })
    seen_nodes.add(equipment_class_id)

    # 2. Add Component Nodes under Class
    components = [
        ("comp_detector", "Component: Detector", "#06B6D4"),
        ("comp_pump", "Component: Pump", "#F59E0B"),
        ("comp_autoinjector", "Component: Auto-Injector", "#10B981"),
        ("comp_column", "Component: Column", "#8B5CF6"),
        ("comp_datasystem", "Component: Data System", "#EC4899")
    ]

    for comp_id, comp_label, comp_color in components:
        if comp_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": comp_id,
                    "label": comp_label,
                    "type": "component",
                    "color": comp_color
                }
            })
            seen_nodes.add(comp_id)
            edges.append({
                "data": {
                    "source": comp_id,
                    "target": equipment_class_id,
                    "label": "HAS_COMPONENT"
                }
            })

    # 3. Connect Record Telemetry & Extracted Fields to Components
    for rec in records:
        rec_id = rec["record_id"]
        data = rec["data"]
        sample_id = data.get("Sample_ID", "UNKNOWN_SAMPLE")
        analyte = data.get("Analyte_Name", "Unknown Compound")
        vendor = data.get("Equipment_Vendor", "Generic Instrument")
        status = rec.get("verification_status", "PASSED")

        detector_data = data.get("detector", {}) if isinstance(data.get("detector"), dict) else {}
        pump_data = data.get("pump", {}) if isinstance(data.get("pump"), dict) else {}
        injector_data = data.get("auto_injector", {}) if isinstance(data.get("auto_injector"), dict) else {}
        column_data = data.get("column", {}) if isinstance(data.get("column"), dict) else {}
        datasys_data = data.get("data_system", {}) if isinstance(data.get("data_system"), dict) else {}

        # ---------------------------------------------------------------
        # A. DETECTOR FIELDS -> Detector Component
        # ---------------------------------------------------------------
        det_type = detector_data.get("Detector_Type", "UV-VIS")
        wl = detector_data.get("Wavelength", 254.0)
        det_node_id = f"det_field_{rec_id}"
        if det_node_id not in seen_nodes:
            det_label = f"Detector ({det_type}): {wl}nm"
            if det_type == "PDA":
                diodes = detector_data.get("Number_of_Diodes", 512)
                det_label += f", {diodes} Diodes"
            nodes.append({
                "data": {
                    "id": det_node_id,
                    "label": det_label,
                    "type": "field_detector",
                    "color": "#38BDF8"
                }
            })
            seen_nodes.add(det_node_id)
            edges.append({
                "data": {
                    "source": det_node_id,
                    "target": "comp_detector",
                    "label": "CONFIGURED_IN"
                }
            })

        # ---------------------------------------------------------------
        # B. PUMP FIELDS -> Pump Component
        # ---------------------------------------------------------------
        flow = pump_data.get("Flow_Rate", 1.0)
        p_type = pump_data.get("Pump_Type", "Binary")
        pump_node_id = f"pump_field_{rec_id}"
        if pump_node_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": pump_node_id,
                    "label": f"Pump ({p_type}): {flow} mL/min",
                    "type": "field_pump",
                    "color": "#FBBF24"
                }
            })
            seen_nodes.add(pump_node_id)
            edges.append({
                "data": {
                    "source": pump_node_id,
                    "target": "comp_pump",
                    "label": "OPERATES_AT"
                }
            })

        # ---------------------------------------------------------------
        # C. AUTO-INJECTOR FIELDS -> Auto-Injector Component
        # ---------------------------------------------------------------
        vial = injector_data.get("Vial_Position", "1:A,1")
        inj_vol = data.get("Injection_Volume", 10.0)
        inj_node_id = f"inj_field_{rec_id}"
        if inj_node_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": inj_node_id,
                    "label": f"Vial: {vial} ({inj_vol} µL)",
                    "type": "field_autoinjector",
                    "color": "#34D399"
                }
            })
            seen_nodes.add(inj_node_id)
            edges.append({
                "data": {
                    "source": inj_node_id,
                    "target": "comp_autoinjector",
                    "label": "LOADED_IN"
                }
            })

        # ---------------------------------------------------------------
        # D. COLUMN FIELDS -> Column Component
        # ---------------------------------------------------------------
        col_model = column_data.get("Col_Model", "C18 Reverse Phase")
        col_temp = column_data.get("Col_Temperature", 30.0)
        col_node_id = f"col_field_{rec_id}"
        if col_node_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": col_node_id,
                    "label": f"Column: {col_model} ({col_temp}°C)",
                    "type": "field_column",
                    "color": "#A78BFA"
                }
            })
            seen_nodes.add(col_node_id)
            edges.append({
                "data": {
                    "source": col_node_id,
                    "target": "comp_column",
                    "label": "MOUNTED_ON"
                }
            })

        # ---------------------------------------------------------------
        # E. CENTRAL ANALYTE PIVOT NODE & CHROMATOGRAM RUNS
        # ---------------------------------------------------------------
        clean_sample_id = sample_id.strip() if isinstance(sample_id, str) else ""
        is_header = (
            not clean_sample_id or 
            clean_sample_id == "UNKNOWN_SAMPLE" or 
            clean_sample_id.lower().startswith("component name") or 
            "ret. time" in clean_sample_id.lower() or 
            "peak area" in clean_sample_id.lower()
        )
        sample_key = analyte if is_header else clean_sample_id
        sample_node_id = f"sample_{sample_key.lower().replace(' ', '_').replace('/', '_').replace(',', '_').replace('\t', '_')}"
        
        if sample_node_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": sample_node_id,
                    "label": f"★ Analyte: {sample_key}",
                    "type": "analyte_central",
                    "sample_name": sample_key,
                    "color": "#F97316"
                }
            })
            seen_nodes.add(sample_node_id)
            
            edges.append({
                "data": {
                    "source": sample_node_id,
                    "target": equipment_class_id,
                    "label": "ANALYZED_IN_CLASS"
                }
            })

        # Molecule (Structure) Node
        analyte_id = f"mol_{analyte.lower().replace(' ', '_').replace('/', '_')}"
        if analyte_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": analyte_id,
                    "label": f"Structure: {analyte}",
                    "type": "molecule",
                    "color": "#10B981"
                }
            })
            seen_nodes.add(analyte_id)
            edges.append({
                "data": {
                    "source": sample_node_id,
                    "target": analyte_id,
                    "label": "IDENTIFIES_STRUCTURE"
                }
            })

        # Method Node
        software = datasys_data.get("Acquisition_Software", "CDS Platform")
        operator = datasys_data.get("Operator", "Analyst")
        method_node_id = f"method_field_{rec_id}"
        if method_node_id not in seen_nodes:
            nodes.append({
                "data": {
                    "id": method_node_id,
                    "label": f"Method: {software} ({operator})",
                    "type": "field_datasystem",
                    "color": "#F472B6"
                }
            })
            seen_nodes.add(method_node_id)
            edges.append({
                "data": {
                    "source": method_node_id,
                    "target": "comp_datasystem",
                    "label": "MANAGED_BY"
                }
            })

        # Peak / Run Node for this System Condition
        peak_node_id = f"peak_{rec_id}"
        rt = data.get("Retention_Time", 0)
        area = data.get("Peak_Area", 0)
        tailing = data.get("Tailing_Factor", 1.0)
        plates = data.get("Plate_Count", 2500)
        rsd = data.get("Percent_RSD", 0.5)

        node_color = "#EF4444" if status == "QUARANTINED" else ("#F59E0B" if status == "FLAGGED" else "#8B5CF6")
        
        nodes.append({
            "data": {
                "id": peak_node_id,
                "label": f"Run [{vendor} {det_type}] (tR:{rt}m)",
                "type": "peak_run",
                "status": status,
                "color": node_color,
                "rec_id": rec_id,
                "det_type": det_type,
                "vendor": vendor,
                "area": area,
                "tailing": tailing,
                "plates": plates,
                "rsd": rsd,
                "col_model": col_model,
                "col_temp": col_temp,
                "flow_rate": flow,
                "wavelength": wl,
                "sample_name": sample_key
            }
        })
        seen_nodes.add(peak_node_id)

        # Connect Central Sample Node to this System Run Node
        edges.append({
            "data": {
                "source": sample_node_id,
                "target": peak_node_id,
                "label": "TESTED_ON_SYSTEM"
            }
        })

        # Connect Peak Run to Telemetry Fields
        edges.append({
            "data": {
                "source": peak_node_id,
                "target": det_node_id,
                "label": "DETECTED_SIGNAL"
            }
        })
        edges.append({
            "data": {
                "source": peak_node_id,
                "target": col_node_id,
                "label": "SEPARATED_ON"
            }
        })
        edges.append({
            "data": {
                "source": peak_node_id,
                "target": pump_node_id,
                "label": "PUMPED_BY"
            }
        })
        edges.append({
            "data": {
                "source": peak_node_id,
                "target": inj_node_id,
                "label": "INJECTED_VIA"
            }
        })

    return {"nodes": nodes, "edges": edges}
