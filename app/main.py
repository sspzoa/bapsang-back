import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from openai import OpenAI
import json
import uuid
import time

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

MAX_RETRIES = 3

@app.post("/chat")
async def chat_with_gpt(request: Request, file: UploadFile = File(...)):
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        base_url = str(request.base_url)
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]
        file_url = f"{base_url}uploads/{unique_filename}"

        text = """
        밥상의 중앙을 기준으로 각 음식들이 몇 시 방향에 있는지 구해줘.
        
        응답은 다른 텍스트 없이 Json 형식으로 해줘 
        
        Ex)
        {
            "흰쌀밥": "7시",
            "된장국": "11시",
            "김치": "8시"
        }
        """

        print(f"Image URL before sending to OpenAI: {file_url}")

        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": text},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": file_url,
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=300
                )

                food_positions = json.loads(response.choices[0].message.content)
                break  # If successful, break out of the retry loop
            except Exception as e:
                if 'Invalid image' in str(e) and attempt < MAX_RETRIES - 1:
                    print(f"Attempt {attempt + 1} failed. Retrying...")
                    time.sleep(1)  # Wait for 1 second before retrying
                else:
                    raise  # If it's not an 'Invalid image' error or we've run out of retries, re-raise the exception

        formatted_response = {
            "food_positions": [
                {"food": food, "position": position}
                for food, position in food_positions.items()
            ]
        }

        return JSONResponse(content=formatted_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse JSON response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))