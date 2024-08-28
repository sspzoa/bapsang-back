import os
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File
from openai import OpenAI
import json

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = FastAPI()

@app.post("/analyze-food-positions")
async def analyze_food_positions(image: UploadFile = File(...)):
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