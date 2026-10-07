import os
import uuid
import zipfile
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session
from app.models import JobModel, CertificateModel
from app.database import SessionLocal

TEMPLATE_DIR = "assets"
TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "certificate_template.png")
OUTPUT_DIR = "generated"

def ensure_template_exists():
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(TEMPLATE_PATH):
        img = Image.new("RGB", (1200, 800), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([30, 30, 1170, 770], outline=(20, 30, 60), width=5)
        draw.text((600, 150), "CERTIFICATE OF COMPLETION", fill=(20, 30, 60), anchor="mm")
        img.save(TEMPLATE_PATH)

def generate_single_certificate(name: str, course: str, output_path: str):
    ensure_template_exists()
    img = Image.open(TEMPLATE_PATH)
    draw = ImageDraw.Draw(img)
    try:
        font_name = ImageFont.load_default()
        font_course = ImageFont.load_default()
    except Exception:
        font_name = None
        font_course = None

    draw.text((600, 380), name, fill=(10, 10, 10), anchor="mm", font=font_name)
    draw.text((600, 520), f"For successfully completing: {course}", fill=(50, 50, 50), anchor="mm", font=font_course)
    img.save(output_path)

def process_certificate_job(job_id: str, recipients: list):
    db: Session = SessionLocal()
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        db.close()
        return

    job.status = "PROCESSING"
    db.commit()

    success_count = 0
    fail_count = 0
    job_folder = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    for item in recipients:
        cert_filename = f"{uuid.uuid4()}.png"
        cert_path = os.path.join(job_folder, cert_filename)

        try:
            if "FAIL_TEST" in item["name"]:
                raise ValueError("Simulated generation failure for testing.")
            generate_single_certificate(item["name"], item["course_name"], cert_path)
            cert_record = CertificateModel(
                job_id=job_id,
                recipient_name=item["name"],
                recipient_email=item["email"],
                course_name=item["course_name"],
                status="SUCCESS",
                file_path=cert_path
            )
            success_count += 1
        except Exception as e:
            cert_record = CertificateModel(
                job_id=job_id,
                recipient_name=item["name"],
                recipient_email=item["email"],
                course_name=item["course_name"],
                status="FAILED",
                error_message=str(e),
                file_path=None
            )
            fail_count += 1

        db.add(cert_record)
        db.commit()

    job.status = "COMPLETED"
    job.successful_count = success_count
    job.failed_count = fail_count
    db.commit()
    db.close()

def create_job_zip(job_id: str) -> str:
    job_folder = os.path.join(OUTPUT_DIR, job_id)
    zip_path = os.path.join(OUTPUT_DIR, f"{job_id}.zip")
    if not os.path.exists(job_folder):
        return None
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(job_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)
    return zip_path
