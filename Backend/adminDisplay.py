import certifi
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from starlette.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# MongoDB configuration
client = MongoClient('mongodb+srv://nani:Nani@cluster0.p71g0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0', tls=True, tlsCAFile=certifi.where())
db = client["Marketing_DB"]
collection = db["Record"]

# Define models
class RecordResponse(BaseModel):
    serial_number: int
    user_name: str
    address:str
    website_url:str
    contact_person:str
    company_name: str
    status: str
    purpose: str
    date_created: str
    image_url: Optional[str] = ""  # URL for the image
    visiting_card_url: Optional[str] = ""  # URL for the visiting card
    location: Optional[str] = ""  # Include location

    class Config:
        orm_mode = True

# Serve static files
router.mount("/static/images", StaticFiles(directory="uploads/images"), name="images")
router.mount("/static/visiting_cards", StaticFiles(directory="uploads/visiting_cards"), name="visiting_cards")

# Ensure directories exist
def ensure_directories_exist():
    os.makedirs("uploads/images", exist_ok=True)
    os.makedirs("uploads/visiting_cards", exist_ok=True)
    logger.info("Ensured that upload directories exist.")

# Call the function to create directories
ensure_directories_exist()

@router.get("/records/", response_model=List[RecordResponse])
async def get_records():
    try:
        records = list(collection.find().sort("upload_time", 1))  # Sort by upload_time in ascending order
        response_data = []

        for record in records:
            # Build URLs for images and visiting cards
            image_url = f"/static/images/{record.get('image_path', '').split('/')[-1]}" if record.get('image_path') else ""
            visiting_card_url = f"/static/visiting_cards/{record.get('visiting_card_path', '').split('/')[-1]}" if record.get('visiting_card_path') else ""
            
            record_data = {
                "serial_number": record["serial_number"],  # Use the serial_number from the record
                "user_name": record.get('user_name', ''),
                "company_name": record.get('company_name', ''),
                "status": record.get('status', ''),
                "purpose": record.get('purpose', ''),
                "date_created": record.get('upload_time', datetime.utcnow().isoformat()),
                "image_url": image_url,
                "visiting_card_url": visiting_card_url,
                "location": record.get('location', '')
            }
            response_data.append(record_data)
        
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Failed to fetch records: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/records/{serial_number}", response_model=RecordResponse)
async def get_record(serial_number: int):
    try:
        record = collection.find_one({"serial_number": serial_number})
        if record:
            # Build URLs for images and visiting cards
            image_url = f"/static/images/{record.get('image_path', '').split('/')[-1]}" if record.get('image_path') else ""
            visiting_card_url = f"/static/visiting_cards/{record.get('visiting_card_path', '').split('/')[-1]}" if record.get('visiting_card_path') else ""
            
            return {
                "serial_number": record["serial_number"],
                "user_name": record["user_name"],
                "company_name": record["company_name"],
                "address": record["address"],  # Ensure this field is included
                "contact_person": record["contact_person"],  # Ensure this field is included
                "website_url": record["website_url"],  # Ensure this field is included
                "status": record["status"],
                "purpose": record["purpose"],
                "upload_time": record["upload_time"],  # Assuming this field exists
                "date_created": record.get('upload_time', datetime.utcnow().isoformat()),
                "location": record["location"],
                "image_url": image_url,
                "visiting_card_url": visiting_card_url,
            }
        else:
            logger.warning(f"Record not found for serial_number: {serial_number}")
            raise HTTPException(status_code=404, detail="Record not found")
    
    except Exception as e:
        logger.error(f"Failed to fetch record with serial_number {serial_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
