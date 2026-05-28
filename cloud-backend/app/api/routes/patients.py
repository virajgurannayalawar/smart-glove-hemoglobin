from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.dependencies import get_current_active_user
from app.services.db import get_database
from app.schemas.patient import PatientCreate, PatientResponse
from datetime import datetime, timezone
import uuid




        

router = APIRouter()

#By setting response_model=PatientResponse, we are telling FastAPI: "No matter what raw data or dictionary comes out of the database, filter and format it so it matches this exact schema before sending it to the user."
@router.post("", response_model=PatientResponse)
async def registser_patient(patient_data: PatientCreate,
      current_user: dict = Depends(get_current_active_user)):
    
    db = get_database()

    owner_id = current_user["owner_id"]
    
    # Check if email already exists for this owner
    existing_patient = await db.patients.find_one(
        {"owner_id": owner_id, "email": patient_data.email}
    )
    if existing_patient:
        raise HTTPException(status_code=409, detail="Email already registered for this owner")
    patient_id = str(uuid.uuid4())  # Unique ID for this patient
    patient_doc = {
        "patient_id": patient_id,
        "owner_id": owner_id,
        "name": patient_data.name,
        "age": patient_data.age,
        "gender": patient_data.gender,
        "contact_number": patient_data.contact_number,
        "email": patient_data.email,
        "notes": patient_data.notes,
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.patients.insert_one(patient_doc)
    patient_doc["_id"] = str(result.inserted_id)
    return patient_doc

@router.get("", response_model=List[PatientResponse])
async def list_patients(
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    db = get_database()
    owner_id = current_user["owner_id"]
    
    # Query patients for this owner, sorted by created_at descending
    cursor = db.patients.find({"owner_id": owner_id}).sort("created_at", -1).skip(skip).limit(limit)
    
    results = []
    async for patient in cursor:
        patient["_id"] = str(patient["_id"])
        results.append(patient)
    
    return results


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
        patient_id: str,
        current_user: dict = Depends(get_current_active_user)
    ):
    db = get_database()
    owner_id = current_user["owner_id"]
    
    # Find patient by patient_id
    required_patient = await db.patients.find_one({"patient_id": patient_id})
    
    if not required_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Authorization check: verify owner
    if required_patient["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this patient")
    
    required_patient["_id"] = str(required_patient["_id"])
    return required_patient

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    db = get_database()
    owner_id = current_user["owner_id"]
    
    # Find patient by patient_id
    patient_to_delete = await db.patients.find_one({"patient_id": patient_id})
    
    if not patient_to_delete:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Authorization check: verify owner
    if patient_to_delete["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this patient")
    
    # Delete patient record
    await db.patients.delete_one({"patient_id": patient_id})
    
    # Optional: Delete related readings
    await db.hemoglobin_readings.delete_many({"patient_id": patient_id})
    
    return {"message": "Patient deleted successfully"}