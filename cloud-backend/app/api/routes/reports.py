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
    OwnerId = current_user["OwnerId"]

    existing = await db.reports.find_one({"OwnerId": OwnerId, "ReadingId": payload.ReadingId})
    if existing:
        existing["_id"] = str(existing["_id"])
        return HemoglobinReportResponse(**existing)

    reading = await db.hemoglobin_readings.find_one({"ReadingId": payload.ReadingId, "OwnerId": OwnerId})
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    patient = await db.patients.find_one({"PatientId": reading["PatientId"], "OwnerId": OwnerId})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    report_id = str(uuid.uuid4())
    scan_ts = reading.get("TrueTimestamp") or reading.get("CreatedAt") or datetime.now(timezone.utc)
    generated_at = datetime.now(timezone.utc)

    report_model = HemoglobinReportResponse(
        _id="",
        ReportId=report_id,
        ReadingId=payload.ReadingId,
        PatientDetails=PatientDetails(
            PatientId=patient["PatientId"],
            Name=patient["Name"],
            Age=int(patient["Age"]),
            Gender=patient["Gender"],
            ContactNumber=patient["ContactNumber"],
            Email=patient["Email"],
            IsPregnant=bool(reading.get("IsPregnant", payload.IsPregnant)),
        ),
        ScannerDetails=ScannerDetails(
            Name=current_user.get("Name", ""),
            Email=current_user.get("Email", ""),
            ContactNumber=current_user.get("ContactNumber", ""),
        ),
        HemoglobinLevel=float(reading["HemoglobinLevel"]),
        IsAnemic=bool(reading.get("IsAnemic")),
        StatusText=reading.get("StatusText") or ("Anemic" if reading.get("IsAnemic") else "Normal"),
        ScanTimestamp=scan_ts,
        ReportGeneratedAt=generated_at,
        PdfUrl=None,
    )

    pdf_bytes = render_hemoglobin_report_pdf(report_model)
    public_id = f"smart-glove/{OwnerId}/reports/{report_id}"
    try:
        pdf_public_id = storage_service.upload_bytes(pdf_bytes, public_id, resource_type="raw")
        pdf_url = storage_service.generate_signed_url(pdf_public_id, resource_type="raw")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload report PDF")

    report_doc = report_model.model_dump(by_alias=True)
    report_doc.update(
        {
            "OwnerId": OwnerId,
            "PatientId": patient["PatientId"],
            "PdfPublicId": pdf_public_id,
            "PdfUrl": pdf_url,
            "ReportGeneratedAt": generated_at,
        }
    )

    res = await db.reports.insert_one(report_doc)
    report_doc["_id"] = str(res.inserted_id)
    return HemoglobinReportResponse(**report_doc)


@router.get("/{report_id}", response_model=HemoglobinReportResponse)
async def get_report(report_id: str, current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    OwnerId = current_user["OwnerId"]

    report = await db.reports.find_one({"OwnerId": OwnerId, "ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report["_id"] = str(report["_id"])
    return HemoglobinReportResponse(**report)


@router.get("", response_model=list[HemoglobinReportResponse])
async def list_reports(current_user: dict = Depends(get_current_active_user), limit: int = 50):
    db = get_database()
    OwnerId = current_user["OwnerId"]
    cursor = db.reports.find({"OwnerId": OwnerId}).sort("ReportGeneratedAt", -1).limit(limit)
    results: list[dict] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return [HemoglobinReportResponse(**r) for r in results]

