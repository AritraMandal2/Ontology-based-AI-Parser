"""
Automated Unit Tests for Multi-Component Chromatography Ontology Extraction Engine.
"""

import unittest
from app.chromatography_ontology import ChromatographyExtraction, UVVisDetectorComponent, PDADetectorComponent
from app.ingestion import calculate_sha256
from app.extractor import extract_with_rules_fallback
from app.verification import verify_and_reconcile_record, approve_hitl_quarantine

class TestMultiComponentChromatographyOntology(unittest.TestCase):

    def test_sha256_calculation(self):
        text = "Sample Name: TEST_01\nArea: 1000"
        hash_val = calculate_sha256(text)
        self.assertEqual(len(hash_val), 64)

    def test_pydantic_component_ontology_schema(self):
        sample = ChromatographyExtraction(
            Sample_ID="SAMPLE_COMP_01",
            Analyte_Name="Paracetamol",
            Equipment_Vendor="Waters",
            Injection_Volume=5.0,
            Retention_Time=2.88,
            Peak_Area=2105.8,
            Peak_Height=410.15,
            Tailing_Factor=1.18,
            Plate_Count=11200,
            Percent_RSD=0.28,
            detector=PDADetectorComponent(
                System_ID="WAT_ACQUITY_PDA02",
                Detector_Type="PDA",
                Number_of_Diodes=512,
                Spectral_Range="190-800 nm"
            )
        )
        self.assertEqual(sample.Sample_ID, "SAMPLE_COMP_01")
        self.assertEqual(sample.detector.Detector_Type, "PDA")
        self.assertEqual(sample.detector.Number_of_Diodes, 512)

    def test_shimadzu_multi_component_extraction(self):
        shimadzu_text = """
System ID: SHIM_LC2030_UV01
Manufacturer: Shimadzu
Model: Prominence LC-2030C 3D
Detector Type: UV-VIS
Wavelength: 254.0 nm
Pressure: 145.2 bar
Flow Rate: 1.0 mL/min
Vial Position: 1:A,2
Inj Volume (uL): 10.0
Col Model: GIS C18
Col Temperature: 30.0 °C
Sample Name: BATCH_IBU_2026_01
Analyte Name: Ibuprofen API
Ret. Time (min): 4.25
Area (mAU*min): 1450.25
Symmetry Factor: 1.12
N (theoretical plates): 8520
CV (%): 0.45
"""
        extracted, _ = extract_with_rules_fallback(shimadzu_text, "shimadzu.txt")
        self.assertEqual(extracted["Sample_ID"], "BATCH_IBU_2026_01")
        self.assertEqual(extracted["detector"]["Wavelength"], 254.0)
        self.assertEqual(extracted["pump"]["Flow_Rate"], 1.0)
        self.assertEqual(extracted["column"]["Col_Temperature"], 30.0)

    def test_boundary_verification_quarantine(self):
        out_of_spec_data = {
            "Sample_ID": "FAIL_SAMPLE",
            "Analyte_Name": "Degradant B",
            "Equipment_Vendor": "Agilent",
            "Injection_Volume": 10.0,
            "Retention_Time": 5.0,
            "Peak_Area": 500.0,
            "Peak_Height": 50.0,
            "Tailing_Factor": 1.2,
            "Plate_Count": 1800,  # Below 2000
            "Percent_RSD": 2.85   # Exceeds 2.0% limit -> QUARANTINED
        }
        reconciled = verify_and_reconcile_record(out_of_spec_data, "hash12345678")
        self.assertEqual(reconciled["verification_status"], "QUARANTINED")

if __name__ == "__main__":
    unittest.main()
