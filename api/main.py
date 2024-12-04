from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List
import uuid
from dotenv import load_dotenv
import os

# โหลดค่า .env
load_dotenv()

# อ่านค่า Environment Variables
API_KEY = os.getenv("API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# เชื่อมต่อ MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db["papers"]

# สร้าง FastAPI
app = FastAPI()

# API Key Authentication
api_key_header = APIKeyHeader(name="X-API-Key")

def authenticate(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

# Schema สำหรับข้อมูล Paper
class Paper(BaseModel):
    title: str = Field(..., example="Understanding Market Trends")
    publish_date: str = Field(..., example="2023-12-01")
    description: str = Field(..., max_length=1000, example="A detailed paper on market trends.")
    source: str = Field(..., example="https://example.com/paper")
    index: str = Field(..., example="nasdaq")

class PaperResponse(Paper):
    paper_id: str

# POST: เพิ่มข้อมูลเข้า MongoDB
@app.post("/papers", response_description="Add new paper", response_model=PaperResponse)
async def add_paper(paper: Paper, api_key: str = Depends(authenticate)):
    paper_id = str(uuid.uuid4())
    data = {**paper.dict(), "paper_id": paper_id}
    collection.insert_one(data)
    return data

# GET: ดึงข้อมูลทั้งหมดจาก MongoDB
@app.get("/papers", response_model=List[PaperResponse], response_description="Get all papers")
async def get_papers(api_key: str = Depends(authenticate)):
    papers = list(collection.find({}, {"_id": 0}))
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found")
    return papers

# GET: ดึงข้อมูลตามดัชนี (Index)
@app.get("/papers/{index}", response_model=List[PaperResponse], response_description="Get papers by index")
async def get_papers_by_index(index: str, api_key: str = Depends(authenticate)):
    papers = list(collection.find({"index": index}, {"_id": 0}))
    if not papers:
        raise HTTPException(status_code=404, detail=f"No papers found for index {index}")
    return papers

# DELETE: ลบข้อมูลโดยใช้ paper_id
@app.delete("/papers/{paper_id}", response_description="Delete a paper")
async def delete_paper(paper_id: str, api_key: str = Depends(authenticate)):
    result = collection.delete_one({"paper_id": paper_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Paper with ID {paper_id} not found")
    return {"message": f"Paper with ID {paper_id} deleted successfully"}
