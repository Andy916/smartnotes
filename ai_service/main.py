from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# 1. Import the specific model-loading tools
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import boto3

app = FastAPI()

print("Loading AI Model and Tokenizer into memory...")
# 2. Explicitly load the model using its exact architectural class
model_name = "sshleifer/distilbart-cnn-12-6"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print("AI Model loaded successfully!")

class NoteRequest(BaseModel):
    title: str
    content: str

# Clean environment variable lookups (safe for GitHub!)
import os
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = "andy-smartnotes-storage-test"

@app.get("/")
def health_check():
    return {"status": "FastAPI AI service is online!"}


@app.post("/summarize")
def summarize_note(request_data: NoteRequest):
    note_content = request_data.content
    
    if len(note_content.split()) < 10:
        raise HTTPException(
            status_code=400, 
            detail="Text is too short to summarize. Please provide at least 10 words."
        )

    try:
        print(f"Processing AI Summary for: {request_data.title}")
        
        # 1. Convert raw text into numbers (tokens) the math model understands
        inputs = tokenizer(note_content, max_length=1024, return_tensors="pt", truncation=True)
        
        # 2. Generate the mathematical summary numbers
        summary_ids = model.generate(inputs["input_ids"], max_length=50, min_length=10, length_penalty=2.0, num_beams=4, early_stopping=True)
        
        # 3. Translate those numbers back into a human-readable English string
        summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # 4. Spin up the AWS client and push the AI summary to S3!
        s3 = boto3.client(
            "s3",
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )

        # 🔥 THE CRITICAL MISSING LINK: You must tell the client to upload the data!
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"ai_summaries/{request_data.title}-summary.txt",
            Body=summary_text
        )
        
        return {
            "title": request_data.title,
            "original_length": len(note_content),
            "summary": summary_text,
            "cloud_destination": f"ai_summaries/{request_data.title}-summary.txt"
        }
        
    except Exception as e:
        print(f"AI Model Error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"The AI model failed to process this text. Error: {str(e)}"
        )