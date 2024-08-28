import os
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import List
from openai import OpenAI
import json

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

app = FastAPI(
    title="밥상 API",
    description="이 API는 밥상 이미지를 분석하여 각 음식의 위치를 시계 방향으로 식별하고 반환합니다.",
    version="1.0.0"
)

security = HTTPBearer()

class FoodPosition(BaseModel):
    food: str
    position: str

class AnalysisResponse(BaseModel):
    food_positions: List[FoodPosition]

class ErrorResponse(BaseModel):
    detail: str

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.credentials

@app.post("/analyze-food-positions",
          response_model=AnalysisResponse,
          summary="밥상 이미지 분석",
          description="업로드된 밥상 이미지에서 각 음식의 위치를 시계 방향으로 분석합니다.",
          response_description="각 음식의 이름과 시계 방향 위치를 포함하는 JSON 객체",
          responses={
              200: {"model": AnalysisResponse, "description": "성공적으로 분석된 결과"},
              401: {"model": ErrorResponse, "description": "인증 실패"},
              500: {"model": ErrorResponse, "description": "서버 내부 오류 (OpenAI API 오류 포함)"}
          })
async def analyze_food_positions(
        image: UploadFile = File(..., description="분석할 밥상 이미지 파일"),
        _: str = Depends(verify_token)
):
    try:
        image_content = await image.read()
        b64_image = base64.b64encode(image_content).decode('utf-8')

        prompt = """
        밥상의 중앙을 기준으로 각 음식들이 몇 시 방향에 있는지 구해줘.
        
        응답은 다른 텍스트 없이 Json 형식으로 해줘 
        
        Ex)
        {
            "흰쌀밥": "7시",
            "된장국": "11시",
            "김치": "8시"
        }
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=300
        )

        result = json.loads(response.choices[0].message.content)
        return {"food_positions": [{"food": k, "position": v} for k, v in result.items()]}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse JSON response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))