import os
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from openai import OpenAI
import json
import uuid
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def is_url_accessible(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException:
        return False

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

        logger.info(f"Generated file URL: {file_url}")

        if not is_url_accessible(file_url):
            raise HTTPException(status_code=500, detail="Generated URL is not accessible")

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
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

        logger.info(f"OpenAI API response: {response}")

        food_positions = json.loads(response.choices[0].message.content)

        formatted_response = {
            "food_positions": [
                {"food": food, "position": position}
                for food, position in food_positions.items()
            ]
        }

        return JSONResponse(content=formatted_response)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise HTTPException(status_code=500, detail="Failed to parse JSON response")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))