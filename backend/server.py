import os
import json
import uuid
import boto3
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from mangum import Mangum
from botocore.exceptions import ClientError

# 1. Setup & Environment
load_dotenv()
app = FastAPI()

# Configure CORS for your CloudFront URL
origins = os.getenv("CORS_ORIGINS", "https://d1iivralq4q3sz.cloudfront.net").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 2. AWS Client Initialization
region = os.getenv("DEFAULT_AWS_REGION", "us-east-1")
bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=region)
s3_client = boto3.client("s3", region_name=region)

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
S3_BUCKET = os.getenv("S3_BUCKET", "twin-memory-ragive")
USE_S3 = os.getenv("USE_S3", "true").lower() == "true"
MEMORY_DIR = "/tmp/memory" 

# Load your persona prompt from context.py
try:
    from context import prompt
except ImportError:
    prompt = "You are James Ragive Dominique, a Cloud Architect and AI Engineer."

# 3. Data Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# 4. Persistence Logic (S3)
def load_conversation(session_id: str) -> List[Dict]:
    if USE_S3:
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=f"memory/{session_id}.json")
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey': return []
            raise e
    return []

def save_conversation(session_id: str, history: List[Dict]):
    if USE_S3:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=f"memory/{session_id}.json",
            Body=json.dumps(history),
            ContentType="application/json"
        )

# 5. The Chat Logic
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Load history and format for Amazon Nova
        history = load_conversation(session_id)
        
        formatted_messages = []
        for msg in history:
            formatted_messages.append({
                "role": msg["role"],
                "content": [{"text": msg["content"]}]
            })
            
        formatted_messages.append({
            "role": "user",
            "content": [{"text": request.message}]
        })

        # --- FIX APPLIED HERE ---
        # If 'prompt' is the function from context.py, call it. 
        # If it's the fallback string from the except block, use it as is.
        system_content = prompt() if callable(prompt) else prompt

        # Call Bedrock Runtime
        body = json.dumps({
            "messages": formatted_messages,
            "system": [{"text": system_content}],
            "inferenceConfig": {"temperature": 0.7, "maxNewTokens": 1000}
        })

        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=body
        )

        # Process the response
        response_body = json.loads(response.get("body").read())
        assistant_text = response_body["output"]["message"]["content"][0]["text"]

        # Save to memory
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": assistant_text})
        save_conversation(session_id, history)

        return ChatResponse(response=assistant_text, session_id=session_id)

    except Exception as e:
        print(f"Server Error: {str(e)}") 
        # Returning str(e) temporarily helps debugging; change back to generic 
        # message once you confirm it works.
        raise HTTPException(status_code=500, detail=str(e))

# 6. Lambda Entry Point
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)