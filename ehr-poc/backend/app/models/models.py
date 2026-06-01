from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


def gen_id():
    return str(uuid.uuid4())


class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=gen_id)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(String)
    gender = Column(String)
    mrn = Column(String, unique=True)
    allergies = Column(JSON, default=list)
    past_medical_history = Column(JSON, default=list)
    medication_history = Column(JSON, default=list)

    encounters = relationship("Encounter", back_populates="patient")


class Encounter(Base):
    __tablename__ = "encounters"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    admission_date = Column(DateTime)
    discharge_date = Column(DateTime, nullable=True)
    status = Column(String)
    primary_diagnosis = Column(String)
    admission_reason = Column(String)

    patient = relationship("Patient", back_populates="encounters")
    observations = relationship("Observation", back_populates="encounter")
    medications = relationship("Medication", back_populates="encounter")
    diagnostic_reports = relationship("DiagnosticReport", back_populates="encounter")
    procedures = relationship("Procedure", back_populates="encounter")
    clinical_notes = relationship("ClinicalNote", back_populates="encounter")
    discharge_summaries = relationship("DischargeSummary", back_populates="encounter")


class Observation(Base):
    __tablename__ = "observations"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"))
    timestamp = Column(DateTime)
    type = Column(String)
    code = Column(String)
    display = Column(String)
    value = Column(Float, nullable=True)
    value_string = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    status = Column(String, default="final")

    encounter = relationship("Encounter", back_populates="observations")


class Medication(Base):
    __tablename__ = "medications"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"))
    timestamp = Column(DateTime)
    name = Column(String)
    dose = Column(String)
    route = Column(String)
    frequency = Column(String)
    status = Column(String)
    indication = Column(String, nullable=True)

    encounter = relationship("Encounter", back_populates="medications")


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"))
    timestamp = Column(DateTime)
    category = Column(String)
    code = Column(String)
    display = Column(String)
    findings = Column(Text)
    conclusion = Column(Text)
    status = Column(String, default="final")

    encounter = relationship("Encounter", back_populates="diagnostic_reports")


class Procedure(Base):
    __tablename__ = "procedures"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"))
    timestamp = Column(DateTime)
    code = Column(String)
    display = Column(String)
    status = Column(String)
    performer = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    encounter = relationship("Encounter", back_populates="procedures")


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"))
    timestamp = Column(DateTime)
    type = Column(String)
    author = Column(String)
    subject = Column(String)
    content = Column(Text)

    encounter = relationship("Encounter", back_populates="clinical_notes")


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"
    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"))
    created_at = Column(DateTime)
    summary_text = Column(Text)
    structured_data = Column(JSON, nullable=True)
    generated_by = Column(String, default="manual")

    encounter = relationship("Encounter", back_populates="discharge_summaries")
