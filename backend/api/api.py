from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
from fastapi.responses import FileResponse

app = FastAPI()


# Initialize state at startup
@app.on_event("startup")
def init_state():
    if not hasattr(app.state, "last_uploaded_filename"):
        app.state.last_uploaded_filename = None

UPLOAD_DIR = "backend/api/bom_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def secure_filename(filename: str) -> str:
    # Remove path info and prepend a UUID to avoid collisions
    name = os.path.basename(filename)
    unique_name = f"{uuid.uuid4().hex}_{name}"
    return unique_name

@app.post("/api/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    if not (file.filename.lower().endswith('.csv') or file.filename.lower().endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or XLSX files are allowed.")
    safe_filename = secure_filename(file.filename)
    file_location = os.path.join(UPLOAD_DIR, safe_filename)
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()
    # Save the uploaded filename to a variable for later use
    app.state.last_uploaded_filename = os.path.join(UPLOAD_DIR, safe_filename)
    return {"filename": safe_filename, "message": "File uploaded successfully."}

@app.post("/api/parse/")
async def parse():
    # Replace this with the function you want to trigger
    if not app.state.last_uploaded_filename:
        raise HTTPException(status_code=400, detail="No CSV file uploaded yet.")
    from backend.parser.parser_agent import parser_agent
    app.state.optimized_bom = parser_agent(csv=app.state.last_uploaded_filename)
    result = {"message": "Action triggered successfully."}
    # Reset the last uploaded filename after parsing
    app.state.last_uploaded_filename = None
    return JSONResponse(content=result)

@app.post("/api/reset/")
async def reset():
    app.state.last_uploaded_filename = None
    return {"message": "State reset successfully."}

@app.get("/api/download_optimized_bom/")
async def download_optimized_bom():
    optimized_bom = getattr(app.state, "optimized_bom", None)
    if not optimized_bom or not os.path.isfile(optimized_bom):
        raise HTTPException(status_code=404, detail="Optimized BOM file not found.")
    filename = os.path.basename(optimized_bom)
    return FileResponse(
        path=optimized_bom,
        filename=filename,
        media_type="application/octet-stream"
    )


if __name__ == "__main__":
    import uvicorn
    from fastapi import Form
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
