import os
import json
import uuid
import boto3
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from mangum import Mangum
from openai import OpenAI
from botocore.exceptions import ClientError

# 1. Setup & Environment
load_dotenv()
app = FastAPI()

origins = os.getenv("CORS_ORIGINS", "https://d1iivralq4q3sz.cloudfront.net").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 2. Client Initialization
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
s3_client = boto3.client("s3", region_name=os.getenv("DEFAULT_AWS_REGION", "us-east-1"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
S3_BUCKET = os.getenv("S3_BUCKET", "twin-memory-ragive")
USE_S3 = os.getenv("USE_S3", "true").lower() == "true"

# Load persona prompt
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
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return []
            raise e
    return []

def save_conversation(session_id: str, history: List[Dict]):
    if USE_S3:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=f"memory/{session_id}.json",
            Body=json.dumps(history),
            ContentType="application/json",
        )

# 5. Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    try:
        history = load_conversation(session_id)
        system_content = prompt() if callable(prompt) else prompt

        # Build OpenAI message list (system + history + new message)
        messages: List[Dict] = [{"role": "system", "content": system_content}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": request.message})

        # Call OpenAI
        completion = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        assistant_text = completion.choices[0].message.content

        # Persist conversation
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": assistant_text})
        save_conversation(session_id, history)

        return ChatResponse(response=assistant_text, session_id=session_id)

    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 6. Lambda Entry Point
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
