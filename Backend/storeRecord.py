from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from pymongo import MongoClient
from fastapi import APIRouter
import os
import shutil
import uuid

app = FastAPI()
router = APIRouter()

# MongoDB connection setup
client = MongoClient('mongodb+srv://nani:Nani@cluster0.p71g0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client["Marketing_DB"]
collection = db["Record"]

# Define a Pydantic model for data validation
class FormData(BaseModel):
    user_name: str
    company_name: str
    address: str
    contact_person: str
    website_url: Optional[str] = ''
    purpose: str
    status: str
    upload_time: str
    location: Optional[str] = ''
    serial_number: Optional[int] = None  # Serial number field

@router.post("/submit_form/")
async def submit_form(
    user_name: str = Form(...),
    company_name: str = Form(...),
    address: str = Form(...),
    contact_person: str = Form(...),
    website_url: Optional[str] = Form(''),
    purpose: str = Form(...),
    status: str = Form(...),
    upload_time: str = Form(...),
    location: Optional[str] = Form(''),
    image_upload: UploadFile = File(...),
    visiting_card: Optional[UploadFile] = File(None)
):
    # Determine the next serial number
    last_record = collection.find_one(sort=[("serial_number", -1)])  # Get the highest serial number
    serial_number = last_record["serial_number"] + 1 if last_record else 1  # Start from 1

    # Prepare the form data
    form_data = {
        "user_name": user_name,
        "company_name": company_name,
        "address": address,
        "contact_person": contact_person,
        "website_url": website_url,
        "purpose": purpose,
        "status": status,
        "upload_time": upload_time,
        "location": location,
        "serial_number": serial_number,
        
    }

    # Save the image file
    if image_upload:
        image_dir = "uploads/images/"
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, image_upload.filename)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image_upload.file, f)
        form_data["image_path"] = image_path

    # Save the visiting card file
    if visiting_card:
        visiting_card_dir = "uploads/visiting_cards/"
        os.makedirs(visiting_card_dir, exist_ok=True)
        visiting_card_path = os.path.join(visiting_card_dir, visiting_card.filename)
        with open(visiting_card_path, "wb") as f:
            shutil.copyfileobj(visiting_card.file, f)
        form_data["visiting_card_path"] = visiting_card_path
 
    # Insert the form data into MongoDB
    result = collection.insert_one(form_data)
   
    return {"status": "success", "data_id": str(result.inserted_id), "serial_number": serial_number}


