from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from fastapi.responses import StreamingResponse
import io
import csv

# Load environment variables in development
if os.getenv('ENVIRONMENT') != 'production':
    from dotenv import load_dotenv
    load_dotenv()

# อ่านค่า Environment Variables
API_KEY = os.getenv("API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# เชื่อมต่อ MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db["research_papers"]

# สร้าง FastAPI
app = FastAPI()

# API Key Authentication
api_key_header = APIKeyHeader(name="X-API-Key")

def authenticate(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

# Schema สำหรับข้อมูล Paper
class Citation(BaseModel):
    period: str = Field(..., example="2020 - 2023")
    count: int = Field(..., example=484)

class Paper(BaseModel):
    title: str = Field(..., example="Social Enterprise Journal")
    citation_per_year: List[Dict[str, int]] = Field(
        ..., 
        example=[
            {"2020 - 2023": 484},
            {"2019 - 2022": 484},
            {"2018 - 2021": 435},
            {"2017 - 2020": 323},
            {"2016 - 2019": 133},
            {"2015 - 2018": 51}
        ]
    )
    published_year: str = Field(..., example="2012")

# Schema สำหรับการตอบกลับ Paper
class PaperResponse(BaseModel):
    title: str
    citation_per_year: List[Dict[str, int]]
    published_year: str
    paper_id: str

@app.get("/papers/csv", response_description="Get all papers in CSV format")
async def get_papers_csv(api_key: str = Depends(authenticate)):
    # Fetch all papers from MongoDB
    papers = list(collection.find({}, {"_id": 0}))  # Exclude the _id field
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found")

    # Define the CSV column names
    columns = [
        "title",
        "2020 - 2023",
        "2019 - 2022",
        "2018 - 2021",
        "2017 - 2020",
        "2016 - 2019",
        "2015 - 2018",
        "2014 - 2017",
        "2013 - 2016",
        "2012 - 2015",
        "2011 - 2014",
        "2010 - 2013",
        "2009 - 2012",
        "2008 - 2011",
    ]

    # Create an in-memory CSV file
    csv_file = io.StringIO()
    csv_writer = csv.DictWriter(csv_file, fieldnames=columns)
    csv_writer.writeheader()

    # Transform MongoDB documents into rows for CSV
    for paper in papers:
        row = {"title": paper["title"]}
        for year_range in columns[1:]:  # Skip the title column
            # Find the citation value for the year range
            citation = next(
                (item[year_range] for item in paper.get("citation_per_year", []) if year_range in item),
                0,  # Default to 0 if year range is not found
            )
            row[year_range] = citation
        csv_writer.writerow(row)

    # Move to the start of the file
    csv_file.seek(0)

    # Return the CSV file as a response
    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=papers.csv"}
    )


# DELETE: Delete a paper by title
@app.delete("/papers/title/{title}", response_description="Delete a paper by title")
async def delete_paper_by_title(title: str, api_key: str = Depends(authenticate)):
    result = collection.delete_one({"title": title})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Paper with title '{title}' not found")
    return {"message": f"Paper with title '{title}' deleted successfully"}

