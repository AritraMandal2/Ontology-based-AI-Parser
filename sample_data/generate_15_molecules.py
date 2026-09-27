"""
Script to generate 15 authentic chromatography datasets across 15 different known molecules,
15 different instrument makes/models, and multi-format files (TXT, CSV, TSV, JSON, PDF).
"""

import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

os.makedirs("sample_data", exist_ok=True)

# 15 Diverse Molecule Datasets
DATASETS = [
    {
        "filename": "sample_data/01_paracetamol_waters_uplc.tsv",
        "format": "tsv",
        "content": "Sample ID\tComponent Name\tRet. Time (min)\tPeak Area (mAU*s)\tPeak Height (mAU)\tTailing Factor\tTheoretical Plates (N)\tPercent RSD (%)\tSystem ID\tVendor\tDetector Type\tWavelength (nm)\tFlow Rate (mL/min)\nPARACETAMOL_VAL_01\tParacetamol (Acetaminophen)\t2.15\t2450.80\t480.20\t1.08\t9500\t0.18\tWATERS_ACQUITY_UPLC_01\tWaters\tPDA\t243.0\t0.60"
    },
    {
        "filename": "sample_data/02_caffeine_agilent_1290.txt",
        "format": "txt",
        "content": """# Agilent 1290 Infinity II LC System Export
System_ID: AGILENT_1290_02
Equipment_Vendor: Agilent
Detector_Type: UV-VIS
Wavelength: 272.0
Flow_Rate: 1.0
Col_Model: ZORBAX Eclipse Plus C18
Col_Temperature: 35.0
Sample_ID: CAFFEINE_STD_100PPM
Analyte_Name: Caffeine
Retention_Time: 3.42
Peak_Area: 1890.45
Peak_Height: 312.80
Tailing_Factor: 1.12
Theoretical_Plates: 8200
Percent_RSD: 0.22
Operator: Dr. Jane Analyst
"""
    },
    {
        "filename": "sample_data/03_aspirin_agilent_1100.pdf",
        "format": "pdf",
        "pdf_lines": [
            "Agilent 1100 Series HPLC System Report",
            "System ID: AGILENT_1100_HPLC_03",
            "Manufacturer: Agilent Technologies",
            "Model: 1100 Series Quaternary Pump & VW Detector",
            "Detector Type: UV-VIS",
            "Wavelength: 226.0 nm",
            "Flow Rate: 1.2 mL/min",
            "Sample ID: ASPIRIN_TABLET_LOT44",
            "Sample Name: Acetylsalicylic Acid 500mg",
            "Analyte Name: Aspirin (Acetylsalicylic Acid)",
            "Ret. Time (min): 4.18",
            "Area (mAU*s): 2150.30",
            "Height (mAU): 395.10",
            "USP Tailing Factor: 1.15",
            "N (Theoretical Plates): 7600",
            "CV (%): 0.28"
        ]
    },
    {
        "filename": "sample_data/04_ibuprofen_shimadzu_prominence.csv",
        "format": "csv",
        "content": "Sample ID,Component Name,Ret. Time,Peak Area,Peak Height,Tailing Factor,Theoretical Plates,% RSD,System ID,Vendor,Detector Type,Excitation Wavelength,Emission Wavelength\nIBUPROFEN_LOT_88,Ibuprofen,5.65,3100.50,520.40,1.18,6800,0.31,SHIMADZU_LC20AD,Shimadzu,FLD,224.0,290.0"
    },
    {
        "filename": "sample_data/05_metformin_thermo_dionex.txt",
        "format": "txt",
        "content": """# Thermo Fisher Dionex UltiMate 3000 (Chromeleon CDS)
System_ID: THERMO_DIONEX_3000
Equipment_Vendor: Thermo
Detector_Type: UV-VIS
Wavelength: 233.0
Flow_Rate: 0.8
Col_Model: Acclaim 120 C18
Col_Temperature: 30.0
Sample_ID: METFORMIN_API_500MG
Analyte_Name: Metformin Hydrochloride
Retention_Time: 1.85
Peak_Area: 4200.15
Peak_Height: 780.90
Tailing_Factor: 1.04
Theoretical_Plates: 10400
Percent_RSD: 0.12
Operator: QA_Manager_Smith
"""
    },
    {
        "filename": "sample_data/06_ascorbic_acid_metrohm_ic.json",
        "format": "json",
        "data": {
            "Equipment_Class": "Chromatography",
            "Sample_ID": "VITAMIN_C_JUICE_01",
            "Analyte_Name": "Ascorbic Acid (Vitamin C)",
            "Equipment_Vendor": "Metrohm",
            "Injection_Volume": 20.0,
            "Retention_Time": 3.10,
            "Peak_Area": 1450.60,
            "Peak_Height": 280.30,
            "Tailing_Factor": 1.09,
            "Plate_Count": 5400,
            "Percent_RSD": 0.45,
            "detector": {
                "Detector_Type": "Conductivity",
                "System_ID": "METROHM_940_IC",
                "Manufacturer": "Metrohm",
                "Model": "940 Professional IC Vario",
                "Temperature": 30.0
            },
            "pump": {
                "Pump_Type": "Isocratic IC",
                "Flow_Rate": 0.7,
                "Pressure": 120.0
            }
        }
    },
    {
        "filename": "sample_data/07_nicotine_varian_prostar.txt",
        "format": "txt",
        "content": """Varian ProStar 230 HPLC Export
System_ID = VARIAN_PROSTAR_230
Equipment_Vendor = Varian
Detector_Type = UV-VIS
Wavelength = 260.0
Flow_Rate = 1.0
Sample_ID = NICOTINE_EXTRACT_09
Analyte_Name = Nicotine
Retention_Time = 3.95
Peak_Area = 1680.20
Peak_Height = 295.40
Tailing_Factor = 1.22
Theoretical_Plates = 6100
Percent_RSD = 0.38
"""
    },
    {
        "filename": "sample_data/08_chlorpheniramine_waters_alliance.csv",
        "format": "csv",
        "content": "Sample ID,Analyte Name,Retention Time,Peak Area,Peak Height,Tailing Factor,Theoretical Plates,% RSD,Vendor,Detector Type\nCHLORPHEN_BATCH_12,Chlorpheniramine Maleate,4.82,2150.90,360.70,1.14,7900,0.25,Waters,PDA"
    },
    {
        "filename": "sample_data/09_atorvastatin_perkinelmer_flexar.txt",
        "format": "txt",
        "content": """PerkinElmer Flexar HPLC System
System_ID: PERKIN_FLEXAR_01
Equipment_Vendor: PerkinElmer
Detector_Type: UV-VIS
Wavelength: 244.0
Flow_Rate: 1.2
Col_Model: Brownlee C18
Sample_ID: ATORVASTATIN_20MG
Analyte_Name: Atorvastatin Calcium
Retention_Time: 6.45
Peak_Area: 3890.70
Peak_Height: 610.30
Tailing_Factor: 1.06
Theoretical_Plates: 11200
Percent_RSD: 0.19
"""
    },
    {
        "filename": "sample_data/10_amoxicillin_shimadzu_nexera.tsv",
        "format": "tsv",
        "content": "Sample ID\tAnalyte Name\tRetention Time\tPeak Area\tPeak Height\tTailing Factor\tTheoretical Plates\t% RSD\tVendor\tDetector Type\nAMOXICILLIN_CAP_500\tAmoxicillin Trihydrate\t2.92\t2780.40\t490.10\t1.11\t8800\t0.29\tShimadzu\tPDA"
    },
    {
        "filename": "sample_data/11_omeprazole_thermo_vanquish.json",
        "format": "json",
        "data": {
            "Equipment_Class": "Chromatography",
            "Sample_ID": "OMEPRAZOLE_STAB_03",
            "Analyte_Name": "Omeprazole",
            "Equipment_Vendor": "Thermo",
            "Injection_Volume": 5.0,
            "Retention_Time": 5.12,
            "Peak_Area": 2980.10,
            "Peak_Height": 510.80,
            "Tailing_Factor": 1.07,
            "Plate_Count": 9900,
            "Percent_RSD": 0.21,
            "detector": {
                "Detector_Type": "UV-VIS",
                "System_ID": "THERMO_VANQUISH_UHPLC",
                "Wavelength": 302.0
            }
        }
    },
    {
        "filename": "sample_data/12_ethanol_bruker_gc.csv",
        "format": "csv",
        "content": "Sample ID,Analyte Name,Retention Time,Peak Area,Peak Height,Tailing Factor,Theoretical Plates,% RSD,Vendor,Detector Type\nETHANOL_BIO_ASSAY_04,Ethanol (Gas Chromatography),1.45,4850.30,890.60,1.02,12500,0.14,Bruker,FID"
    },
    {
        "filename": "sample_data/13_cannabidiol_hitachi_chromaster.txt",
        "format": "txt",
        "content": """Hitachi Chromaster HPLC Data Export
System_ID: HITACHI_CHROMASTER_5000
Equipment_Vendor: Hitachi
Detector_Type: UV-VIS
Wavelength: 228.0
Flow_Rate: 1.0
Sample_ID: CBD_HEMP_EXTRACT_99
Analyte_Name: Cannabidiol (CBD)
Retention_Time: 6.88
Peak_Area: 3420.80
Peak_Height: 540.20
Tailing_Factor: 1.16
Theoretical_Plates: 8100
Percent_RSD: 0.32
"""
    },
    {
        "filename": "sample_data/14_morphine_knauer_azura.tsv",
        "format": "tsv",
        "content": "Sample ID\tAnalyte Name\tRetention Time\tPeak Area\tPeak Height\tTailing Factor\tTheoretical Plates\t% RSD\tVendor\tDetector Type\nMORPHINE_INJ_10MG\tMorphine Sulfate\t3.15\t1940.60\t340.50\t1.10\t7400\t0.27\tKnauer\tUV-VIS"
    },
    {
        "filename": "sample_data/15_theophylline_jasco_lc4000.pdf",
        "format": "pdf",
        "pdf_lines": [
            "Jasco LC-4000 Series HPLC Analytical Report",
            "System ID: JASCO_LC4000_PDA",
            "Manufacturer: Jasco Corporation",
            "Model: LC-4000 Smart HPLC",
            "Detector Type: PDA",
            "Wavelength: 275.0 nm",
            "Flow Rate: 1.0 mL/min",
            "Sample ID: THEOPHYLLINE_SERUM_01",
            "Analyte Name: Theophylline",
            "Ret. Time (min): 3.65",
            "Area (mAU*s): 2280.90",
            "Height (mAU): 410.60",
            "Tailing Factor: 1.08",
            "N (Theoretical Plates): 8700",
            "CV (%): 0.20"
        ]
    }
]

for ds in DATASETS:
    fn = ds["filename"]
    fmt = ds["format"]
    if fmt == "pdf":
        c = canvas.Canvas(fn, pagesize=letter)
        y = 750
        for line in ds["pdf_lines"]:
            c.drawString(100, y, line)
            y -= 20
        c.save()
        print(f"Generated PDF: {fn}")
    elif fmt == "json":
        with open(fn, "w") as f:
            json.dump(ds["data"], f, indent=2)
        print(f"Generated JSON: {fn}")
    else:
        with open(fn, "w") as f:
            f.write(ds["content"])
        print(f"Generated Text/CSV/TSV: {fn}")

print("All 15 molecule datasets generated successfully!")
