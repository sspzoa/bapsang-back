import os
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from openai import OpenAI
import json

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = FastAPI(
    title="밥상 API",
    description="이 API는 음식 이미지를 분석하여 각 음식의 위치를 시계 방향으로 반환합니다.",
    version="1.0.0"
)

class FoodPosition(BaseModel):
    food: str
    position: str

class AnalysisResponse(BaseModel):
    food_positions: List[FoodPosition]

@app.post("/analyze-food-positions",
          response_model=AnalysisResponse,
          summary="음식 위치 분석",
          description="업로드된 이미지에서 각 음식의 위치를 시계 방향으로 분석합니다.",
          response_description="각 음식의 이름과 위치를 포함하는 JSON 객체")
async def analyze_food_positions(image: UploadFile = File(..., description="분석할 음식 이미지 파일")):
    """
    음식 위치 분석 엔드포인트

    이 엔드포인트는 업로드된 이미지를 분석하여 밥상에서 각 음식의 위치를 시계 방향으로 반환합니다.

    처리 과정:
    1. 업로드된 이미지를 읽습니다.
    2. 이미지를 base64로 인코딩합니다.
    3. OpenAI의 GPT-4 모델을 사용하여 이미지를 분석합니다.
    4. 분석 결과를 파싱하여 구조화된 형식으로 반환합니다.

    오류 처리:
    - JSON 파싱 실패 시 500 에러를 반환합니다.
    - 기타 예외 발생 시 500 에러와 함께 오류 세부 정보를 반환합니다.

    Returns:
        AnalysisResponse: 각 음식의 이름과 해당 위치를 포함하는 객체
    """
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