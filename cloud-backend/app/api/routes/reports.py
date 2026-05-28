from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_active_user
from app.schemas.report import (
    HemoglobinReportCreate,
    HemoglobinReportResponse,
    PatientDetails,
    ScannerDetails,
)
from app.services.cloudinary_service import storage_service
from app.services.db import get_database
from app.services.pdf_reports import render_hemoglobin_report_pdf


router = APIRouter()


@router.post("", response_model=HemoglobinReportResponse)
async def create_report(
    payload: HemoglobinReportCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    owner_id = current_user["owner_id"]

    existing = await db.reports.find_one({"owner_id": owner_id, "reading_id": payload.reading_id})
    if existing:
        existing["_id"] = str(existing["_id"])
        return HemoglobinReportResponse(**existing)

    reading = await db.hemoglobin_readings.find_one({"reading_id": payload.reading_id, "owner_id": owner_id})
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    patient = await db.patients.find_one({"patient_id": reading["patient_id"], "owner_id": owner_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    report_id = str(uuid.uuid4())
    scan_ts = reading.get("true_timestamp") or reading.get("created_at") or datetime.now(timezone.utc)
    generated_at = datetime.now(timezone.utc)

    report_model = HemoglobinReportResponse(
        _id="",
        report_id=report_id,
        reading_id=payload.reading_id,
        patient_details=PatientDetails(
            patient_id=patient["patient_id"],
            name=patient["name"],
            age=int(patient["age"]),
            gender=patient["gender"],
            contact_number=patient["contact_number"],
            email=patient["email"],
            is_pregnant=bool(reading.get("is_pregnant", payload.is_pregnant)),
        ),
        scanner_details=ScannerDetails(
            name=current_user.get("name", ""),
            email=current_user.get("email", ""),
            contact_number=current_user.get("contact_number", ""),
        ),
        hemoglobin_level=float(reading["hemoglobin_level"]),
        is_anemic=bool(reading.get("is_anemic")),
        status_text=reading.get("status_text") or ("Anemic" if reading.get("is_anemic") else "Normal"),
        scan_timestamp=scan_ts,
        report_generated_at=generated_at,
        pdf_url=None,
    )

    pdf_bytes = render_hemoglobin_report_pdf(report_model)
    public_id = f"smart-glove/{owner_id}/reports/{report_id}"
    try:
        pdf_public_id = storage_service.upload_bytes(pdf_bytes, public_id, resource_type="raw")
        pdf_url = storage_service.generate_signed_url(pdf_public_id, resource_type="raw")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload report PDF")

    report_doc = report_model.model_dump(by_alias=True)
    report_doc.update(
        {
            "owner_id": owner_id,
            "patient_id": patient["patient_id"],
            "pdf_public_id": pdf_public_id,
            "pdf_url": pdf_url,
            "report_generated_at": generated_at,
        }
    )

    res = await db.reports.insert_one(report_doc)
    report_doc["_id"] = str(res.inserted_id)
    return HemoglobinReportResponse(**report_doc)


@router.get("/{report_id}", response_model=HemoglobinReportResponse)
async def get_report(report_id: str, current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    owner_id = current_user["owner_id"]

    report = await db.reports.find_one({"owner_id": owner_id, "report_id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report["_id"] = str(report["_id"])
    return HemoglobinReportResponse(**report)


@router.get("", response_model=list[HemoglobinReportResponse])
async def list_reports(current_user: dict = Depends(get_current_active_user), limit: int = 50):
    db = get_database()
    owner_id = current_user["owner_id"]
    cursor = db.reports.find({"owner_id": owner_id}).sort("report_generated_at", -1).limit(limit)
    results: list[dict] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return [HemoglobinReportResponse(**r) for r in results]

