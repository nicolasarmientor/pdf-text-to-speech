from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
import os
from pathlib import Path

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/text-to-speech")
async def transfer(file: UploadFile = File(...), voice: str = Form("alloy")):
    text = ""
    with pdfplumber.open(file.file) as pdf_file:
        for page in pdf_file.pages:
            text += page.extract_text() or ""

    if not text or not text.strip():
        return HTMLResponse("No text found in PDF", status_code=400)
    
    Path("static").mkdir(parents=True, exist_ok=True)
    audio_file_path = Path("static/pdf_to_speech.mp3")

    with client.audio.speech.with_streaming_response.create(
         model="gpt-4o-mini-tts",
         voice=voice,
         input=text,
    ) as response:
        response.stream_to_file(str(audio_file_path))
    
    return FileResponse(
        path=str(audio_file_path),
        media_type="audio/mpeg",
        filename="pdf_to_speech.mp3"
    )