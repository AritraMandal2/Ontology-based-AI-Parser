"""
GxP Hierarchical Equipment Class Ontology for Chromatography.
Class: Chromatography
Components: Detector (UV-Vis, PDA, FLD, RI), Pump, Auto-Injector, Column, Data System.
"""

from typing import Optional, Dict, Any, List, Union, Literal
from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# 1. DETECTOR COMPONENTS (Common + Type Specific)
# ----------------------------------------------------------------------

class CommonDetectorComponent(BaseModel):
    System_ID: Optional[str] = Field(None, description="System ID")
    Manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    Model: Optional[str] = Field(None, description="Model designation")
    Firmware_Version: Optional[str] = Field(None, description="Firmware version")
    Serial_Number: Optional[str] = Field(None, description="Serial number")
    Lab_Location: Optional[str] = Field(None, description="Laboratory location")


class UVVisDetectorComponent(CommonDetectorComponent):
    Detector_Type: Literal["UV-VIS"] = "UV-VIS"
    Wavelength: Optional[float] = Field(None, description="Wavelength in nm")
    Reference_Wavelength: Optional[float] = Field(None, description="Reference Wavelength in nm")
    Bandwidth: Optional[float] = Field(None, description="Bandwidth in nm")
    Path_Length: Optional[float] = Field(None, description="Path Length in mm")
    Temperature: Optional[float] = Field(None, description="Detector Cell Temperature in °C")


class PDADetectorComponent(CommonDetectorComponent):
    Detector_Type: Literal["PDA"] = "PDA"
    Number_of_Diodes: Optional[int] = Field(None, description="Number of diodes")
    Spectral_Range: Optional[str] = Field(None, description="Spectral Range e.g. 190-800 nm")
    Spectral_Resolution: Optional[float] = Field(None, description="Spectral Resolution in nm")
    Time_Sampling_Rate: Optional[float] = Field(None, description="Sampling rate in Hz")
    Slit_Width: Optional[float] = Field(None, description="Slit width in nm")
    Reference_Wavelength: Optional[float] = Field(None, description="Reference Wavelength in nm")
    Path_Length: Optional[float] = Field(None, description="Path Length in mm")
    Baseline_Noise: Optional[float] = Field(None, description="Baseline Noise in µAU")
    Lamp_Type: Optional[str] = Field(None, description="Lamp Type e.g. Deuterium/Tungsten")
    Lamp_Hours: Optional[float] = Field(None, description="Lamp operating hours")
    Temperature: Optional[float] = Field(None, description="Detector Cell Temperature in °C")


class FLDDetectorComponent(CommonDetectorComponent):
    Detector_Type: Literal["FLD"] = "FLD"
    Excitation_Wavelength: Optional[float] = Field(None, description="Excitation Wavelength in nm")
    Emission_Wavelength: Optional[str] = Field(None, description="Emission Wavelength or Range in nm")
    Excitation_Bandwidth: Optional[float] = Field(None, description="Excitation Bandwidth in nm")
    Emission_Bandwidth: Optional[float] = Field(None, description="Emission Bandwidth in nm")
    Voltage: Optional[float] = Field(None, description="PMT Voltage in Volts")
    Lamp_Type: Optional[str] = Field(None, description="Xenon Flash Lamp")
    Lamp_Power: Optional[float] = Field(None, description="Lamp Power in Watts")
    Lamp_Hours: Optional[float] = Field(None, description="Lamp operating hours")
    Temperature: Optional[float] = Field(None, description="Detector Cell Temperature in °C")


class RIDetectorComponent(CommonDetectorComponent):
    Detector_Type: Literal["RI"] = "RI"
    Optical_Wavelength: Optional[float] = Field(None, description="Optical Wavelength in nm")
    Baseline_Noise: Optional[float] = Field(None, description="Baseline Noise in nRIU")
    Baseline_Drift: Optional[float] = Field(None, description="Baseline Drift in nRIU/hr")
    Data_Rate: Optional[float] = Field(None, description="Data acquisition rate in Hz")
    Time_Constant: Optional[float] = Field(None, description="Time Constant in sec")
    Auto_Zero_At_Start: Optional[bool] = Field(True, description="Auto zero baseline at start")
    Cell_Temperature: Optional[float] = Field(None, description="Cell Temperature in °C")


DetectorUnion = Union[
    UVVisDetectorComponent,
    PDADetectorComponent,
    FLDDetectorComponent,
    RIDetectorComponent,
    CommonDetectorComponent
]


# ----------------------------------------------------------------------
# 2. PUMP COMPONENT
# ----------------------------------------------------------------------

class PumpComponent(BaseModel):
    Pump_Type: Optional[str] = Field(None, description="Isocratic, Binary, Quaternary, Dual")
    Pressure: Optional[float] = Field(None, description="System Pressure in bar / psi")
    Flow_Rate: Optional[float] = Field(None, description="Flow Rate in mL/min")
    Gradient_Steps: Optional[List[str]] = Field(default_factory=list, description="Gradient step program")
    Run_Time: Optional[str] = Field(None, description="Total Run Time e.g. 10.0 min")
    Equilibration_Time: Optional[str] = Field(None, description="Equilibration Time e.g. 2.0 min")
    Mobile_Phase_A: Optional[str] = Field(None, description="Mobile phase A solvent")
    Mobile_Phase_B: Optional[str] = Field(None, description="Mobile phase B solvent")
    Mobile_Phase_C: Optional[str] = Field(None, description="Mobile phase C solvent")
    Mobile_Phase_D: Optional[str] = Field(None, description="Mobile phase D solvent")
    Mobile_Phase_Composition: Optional[str] = Field(None, description="Composition ratio e.g. 60:40 A:B")
    pH: Optional[str] = Field(None, description="Mobile phase pH")
    Buffer: Optional[str] = Field(None, description="Buffer salt details")


# ----------------------------------------------------------------------
# 3. AUTO-INJECTOR COMPONENT
# ----------------------------------------------------------------------

class AutoInjectorComponent(BaseModel):
    Injection_ID: Optional[str] = Field(None, description="Unique Injection Identifier")
    Vial_Position: Optional[str] = Field(None, description="Vial position e.g. 1:A,2")
    Sample_ID: Optional[str] = Field(None, description="Sample Identifier")
    Injection_Volume: Optional[float] = Field(None, description="Injection Volume in µL")
    Sequence_ID: Optional[str] = Field(None, description="Sequence / Batch ID")
    Start_Time: Optional[str] = Field(None, description="Injection Start Date Time")
    Replicate: Optional[int] = Field(1, description="Replicate number")


# ----------------------------------------------------------------------
# 4. COLUMN COMPONENT
# ----------------------------------------------------------------------

class ColumnComponent(BaseModel):
    Column_ID: Optional[str] = Field(None, description="Unique Column Identifier / Serial")
    Col_Manufacturer: Optional[str] = Field(None, description="Column Manufacturer")
    Col_Model: Optional[str] = Field(None, description="Column Model Name")
    Col_Lot_Number: Optional[str] = Field(None, description="Column Lot Number")
    Col_Stationary_Phase: Optional[str] = Field(None, description="e.g. C18, C8, Phenyl-Hexyl")
    Col_Length: Optional[float] = Field(None, description="Column Length in mm")
    Col_Temperature: Optional[float] = Field(None, description="Column Compartment Temp in °C")
    Col_Particle_Size: Optional[float] = Field(None, description="Particle Size in µm")
    Col_Pore_Size: Optional[float] = Field(None, description="Pore Size in Å")
    Col_Chemistry: Optional[str] = Field(None, description="Column Chemistry classification")


# ----------------------------------------------------------------------
# 5. DATA SYSTEM COMPONENT
# ----------------------------------------------------------------------

class DataSystemComponent(BaseModel):
    Sample_ID: Optional[str] = Field(None, description="Sample ID")
    Sample_Type: Optional[str] = Field(None, description="Standard, QC, Blank, Unknown, System Suitability")
    Sample_Name: Optional[str] = Field(None, description="Human readable sample name")
    Matrix: Optional[str] = Field(None, description="Sample Matrix e.g. Plasma, Tablet, Solution")
    Preparation: Optional[str] = Field(None, description="Sample preparation protocol")
    Dilution_Factor: Optional[float] = Field(1.0, description="Dilution Factor")
    Internal_Standard_Concentration: Optional[float] = Field(None, description="IS Concentration")
    Sample_Batch_ID: Optional[str] = Field(None, description="Sample Batch ID")
    Method_ID: Optional[str] = Field(None, description="Method Identifier")
    Method_Name: Optional[str] = Field(None, description="Analytical Method Name")
    Method_Version: Optional[str] = Field(None, description="Method Version")
    Acquisition_Software: Optional[str] = Field(None, description="Software Name e.g. Empower 3, Chromeleon")
    Software_Version: Optional[str] = Field(None, description="Software Version")
    Notes: Optional[str] = Field(None, description="Operator notes")
    Operator: Optional[str] = Field(None, description="Analyst / Operator Name")
    Chromatogram_ID: Optional[str] = Field(None, description="Chromatogram Run ID")
    Peak_ID: Optional[str] = Field(None, description="Peak Identification")
    Retention_Time: Optional[float] = Field(None, description="Retention Time in minutes")
    Start_Time: Optional[float] = Field(None, description="Peak Start Time in minutes")
    End_Time: Optional[float] = Field(None, description="Peak End Time in minutes")
    Area: Optional[float] = Field(None, description="Peak Area")
    Area_Unit: Optional[str] = Field("mAU*min", description="Area Unit")
    Height: Optional[float] = Field(None, description="Peak Height")
    Height_Unit: Optional[str] = Field("mAU", description="Height Unit")
    Tailing_Factor: Optional[float] = Field(None, description="Tailing Factor / Symmetry")
    Theoretical_Plates: Optional[float] = Field(None, description="Theoretical Plates (N)")
    Resolution_To_Prev: Optional[float] = Field(None, description="Chromatographic Resolution (Rs)")
    Analyte_ID: Optional[str] = Field(None, description="Analyte Compound Name / ID")
    Peak_Smoothness_Factor: Optional[float] = Field(None, description="Peak Smoothness Factor")


# ----------------------------------------------------------------------
# MAIN ROOT ONTOLOGY CLASS MODEL
# ----------------------------------------------------------------------

class ChromatographyExtraction(BaseModel):
    # Top-Level Equipment Class
    Equipment_Class: Literal["Chromatography"] = "Chromatography"

    # Canonical Core Shortcuts
    Sample_ID: str = Field(..., description="Canonical Sample ID")
    Analyte_Name: str = Field("Unknown Compound", description="Canonical Analyte Name")
    Equipment_Vendor: str = Field("Generic", description="Instrument Vendor")
    Injection_Volume: float = Field(10.0, description="Injection Volume in µL")
    Retention_Time: float = Field(0.0, description="Retention Time in min")
    Peak_Area: float = Field(0.0, description="Peak Area in mAU*min")
    Peak_Height: float = Field(0.0, description="Peak Height in mAU")
    Tailing_Factor: float = Field(1.0, description="Tailing Factor")
    Plate_Count: int = Field(2500, description="Theoretical Plates")
    Percent_RSD: Optional[float] = Field(0.0, description="Precision % RSD")

    # Component Hierarchy Sub-Blocks
    detector: DetectorUnion = Field(default_factory=CommonDetectorComponent)
    pump: PumpComponent = Field(default_factory=PumpComponent)
    auto_injector: AutoInjectorComponent = Field(default_factory=AutoInjectorComponent)
    column: ColumnComponent = Field(default_factory=ColumnComponent)
    data_system: DataSystemComponent = Field(default_factory=DataSystemComponent)


# Extended Vendor Synonym Mapping Table across all 5 Component Sub-Blocks
VENDOR_SYNONYMS: Dict[str, List[str]] = {
    # Data System / Canonical
    "Sample_ID": ["Sample Name", "Sample ID", "Sample", "Vial ID", "Sample Identification", "Sample_ID", "Sample_Name"],
    "Analyte_Name": ["Compound", "Analyte", "Peak Name", "Component Name", "Component", "Target Molecule", "Analyte ID", "Analyte_Name", "Component_Name"],
    "Retention_Time": ["Ret. Time (min)", "Ret. Time", "Ret Time", "Retention Time", "RT", "tR (minutes)", "Retention Time (min)", "RT (min)", "Ret_Time", "Retention_Time", "Ret. Time (min):"],
    "Peak_Area": ["Area", "Peak Area", "Area (mAU*min)", "Peak Area [mAU·min]", "Area [mAU*sec]", "Area (mAU*s)", "Area_uVs", "Peak_Area"],
    "Peak_Height": ["Height", "Peak Height", "Height (mAU)", "Peak Height [mAU]", "Height_uV", "Peak_Height"],
    "Tailing_Factor": ["Tailing Factor", "USP Tailing", "Symmetry Factor", "As (USP)", "Tailing (USP)", "USP Tailing Factor", "Tailing", "Tailing_Factor"],
    "Plate_Count": ["Plate Count", "Plates (USP)", "N (theoretical plates)", "N [USP]", "Theoretical Plates", "Theoretical_Plates", "Plate_Count", "N", "Plates"],
    "Percent_RSD": ["% RSD", "RSD%", "CV (%)", "Rel. Std. Dev. (%)", "%RSD", "RSD_Percent", "RSD"],

    # Detector
    "System_ID": ["System ID", "Instrument ID", "System Name", "System_ID"],
    "Manufacturer": ["Manufacturer", "Make", "Vendor", "Equipment_Vendor"],
    "Model": ["Model", "Detector Model", "Instrument Model"],
    "Detector_Type": ["Detector Type", "Detector", "Det Type", "Det_Type", "Detector_Type", "Det"],
    "Firmware_Version": ["Firmware Version", "Firmware", "FW Rev"],
    "Serial_Number": ["Serial Number", "Serial No", "S/N"],
    "Lab_Location": ["Lab Location", "Location", "Room"],
    "Wavelength": ["Wavelength", "Optical Wavelength", "Excitation Wavelength", "WL (nm)", "Detection Wavelength", "Wavelength (nm)", "WL"],
    "Reference_Wavelength": ["Reference Wavelength", "Ref Wavelength", "Ref WL"],
    "Bandwidth": ["Bandwidth", "BW (nm)", "Excitation Bandwidth", "Emission Bandwidth"],
    "Path_Length": ["Path Length", "Cell Path Length"],
    "Temperature": ["Detector Temperature", "Cell Temperature", "Temp (°C)"],
    "Number_of_Diodes": ["NUMBER OF DIODE", "Number of Diodes", "Diodes"],
    "Spectral_Range": ["SPECTRAL RANGE", "Spectral Range"],
    "Spectral_Resolution": ["SPECTRAL RESOLUTION", "Spectral Resolution"],
    "Baseline_Noise": ["BASELINE NOISE", "Baseline Noise"],
    "Lamp_Type": ["LAMP TYPE", "Lamp Type"],
    "Lamp_Hours": ["LAMP HOUR", "Lamp Hours"],

    # Pump
    "Pump_Type": ["Pump Type", "Pump", "Type"],
    "Pressure": ["Pressure", "System Pressure", "Pressure (bar)", "Pressure (psi)"],
    "Flow_Rate": ["Flow Rate", "Flow Rate (mL/min)", "Flow (mL/min)", "Flow_Rate"],
    "Run_Time": ["Run Time", "Total Run Time"],
    "Equilibration_Time": ["Equilibration Time", "Equil Time"],
    "Mobile_Phase_A": ["Mobile phase A", "Mobile Phase A", "Solvent A"],
    "Mobile_Phase_B": ["Mobile phase B", "Mobile Phase B", "Solvent B"],
    "Mobile_Phase_Composition": ["Mobile phase Composition", "Composition", "Solvent Ratio"],
    "pH": ["pH", "Mobile Phase pH"],
    "Buffer": ["Buffer", "Buffer Details"],

    # Auto Injector
    "Injection_ID": ["Injection ID", "Inj ID"],
    "Vial_Position": ["Vial Position", "Vial", "Position", "Vial_Position"],
    "Injection_Volume": ["Injection Volume", "Inj Volume", "Injection Vol", "Inj Vol (uL)", "Inj Volume (µL)", "Injection_Volume"],
    "Sequence_ID": ["Sequence ID", "Sequence   ID", "Batch ID"],
    "Start_Time": ["Start Time", "Injection Time", "Acquisition Time"],
    "Replicate": ["Replicate", "Inj #"],

    # Column
    "Column_ID": ["Column ID", "Col ID", "Column Serial"],
    "Col_Manufacturer": ["Col Manufacturer", "Column Manufacturer", "Col Make"],
    "Col_Model": ["Col Model", "Column Model", "Column Name", "Column", "Col Type", "Col_Model", "Column Details", "Column_Spec"],
    "Col_Lot_Number": ["Col Lot Number", "Column Lot"],
    "Col_Stationary_Phase": ["Col Stationary Phase", "Stationary Phase", "Phase"],
    "Col_Length": ["Col Length", "Column Length (mm)", "Col_Length"],
    "Col_Temperature": ["Col Temperature", "Column Temperature", "Col Temp", "Column Temp (°C)", "Oven Temp", "Col_Temperature"],
    "Col_Particle_Size": ["Col Particle Size", "Particle Size (µm)", "Col_Particle_Size"],
    "Col_Pore_Size": ["Col Pore Size", "Pore Size (Å)"],
    "Col_Chemistry": ["Col Chemistry", "Chemistry"],

    # Data System
    "Sample_Type": ["Sample Type", "Type"],
    "Sample_Name": ["Sample Name", "Sample Title"],
    "Matrix": ["Matrix", "Sample Matrix"],
    "Preparation": ["Preparation", "Sample Prep"],
    "Dilution_Factor": ["Dilution Factor", "Dilution"],
    "Method_ID": ["Method ID", "Method Name"],
    "Acquisition_Software": ["Acquisition software", "Software", "CDS"],
    "Software_Version": ["Software Version", "SW Version"],
    "Operator": ["Operator", "Analyst", "User"],
    "Resolution_To_Prev": ["Resolution to Prev", "Resolution", "Rs"]
}

# Bounds
DATA_PACKET_BOUNDS = {
    "Injection_Volume": {"min": 0.1, "max": 100.0, "unit": "µL"},
    "Retention_Time": {"min": 0.01, "max": 60.0, "unit": "min"},
    "Plate_Count": {"min_suitability": 2000, "unit": "plates"},
    "Tailing_Factor": {"min_ideal": 0.8, "max_ideal": 2.0, "unit": "unitless"},
    "Percent_RSD": {"max_allowed": 2.0, "unit": "%"},
}
