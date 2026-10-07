import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import JobModel, CertificateModel
from app.schemas import BulkGenerationRequest, JobStatusResponse
from app.services.certificate_service import process_certificate_job, create_job_zip

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificates"])

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def create_bulk_generation_job(
    payload: BulkGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    new_job = JobModel(total_recipients=len(payload.recipients), status="PENDING")
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    recipients_data = [r.model_dump() for r in payload.recipients]
    background_tasks.add_task(process_certificate_job, new_job.id, recipients_data)

    return {
        "job_id": new_job.id,
        "status": new_job.status,
        "total_recipients": new_job.total_recipients,
        "message": "Certificate generation job accepted and processing asynchronously."
    }

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.get("/download/{certificate_id}")
def download_single_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(CertificateModel).filter(CertificateModel.id == certificate_id).first()
    if not cert or not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found.")
    return FileResponse(cert.file_path, media_type="image/png", filename=f"certificate_{cert.recipient_name}.png")

@router.get("/jobs/{job_id}/download-all")
def download_all_certificates(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    zip_path = create_job_zip(job_id)
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="No generated certificates available.")
    return FileResponse(zip_path, media_type="application/zip", filename=f"certificates_job_{job_id}.zip")
