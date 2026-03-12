import requests
import uuid
import time
import json
import google.generativeai as genai 


api_url = ''
secret_key = ''
image_file = 'example.jpg'
GEMINI_API_KEY = ''
genai.configure(api_key=GEMINI_API_KEY)
model=genai.GenerativeModel("gemini-3-flash-preview")

request_json = {
    'images': [
        {
            'format': 'jpg',
            'name': 'example'
        }
    ],
    'requestId': str(uuid.uuid4()),
    'version': 'V2',
    'timestamp': int(round(time.time() * 1000))
}

payload = {
    "message": json.dumps(request_json).encode("UTF-8")
}
files = [
  ('file', open(image_file,'rb'))
]
headers = {
  'X-OCR-SECRET': secret_key
}

response = requests.post(
    api_url,
    headers=headers,
    data=payload,
    files=files
)
result = response.json()

ocr_text_list = []
for i in result['images'][0]['fields']:
    text = i['inferText']
    ocr_text_list.append(text)

ocr_text = " ".join(ocr_text_list)

print("OCR TEXT:")
print(ocr_text)

# Gemini 프롬프트
prompt = f"""
다음은 식품 상세 이미지에서 OCR로 추출한 텍스트입니다.
이 텍스트를 분석하여 데이터를 추출하고 요약해 주세요.

OCR 텍스트:
{ocr_text}

다음 항목을 정리해주세요:
- 제품명
- 식품유형
- 내용량
- 원재료명
- 영양정보
- 알레르기 정보
"""

response_gemini = model.generate_content(prompt)

print("\nGemini 분석 결과:")
print(response_gemini.text)
