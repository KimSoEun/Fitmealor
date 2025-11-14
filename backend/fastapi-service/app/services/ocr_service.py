"""
OCR Service for Korean Food Label Recognition
Optimized for Korean text recognition with allergen detection
"""

import base64
import json
import logging
from typing import Dict, List, Any, Optional
from io import BytesIO
from PIL import Image
import httpx
import re
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class FoodLabelOCRService:
    """
    Korean food label OCR service
    Supports CLOVA OCR and fallback to Tesseract
    """
    
    def __init__(self):
        self.clova_url = settings.CLOVA_OCR_URL
        self.clova_secret = settings.CLOVA_OCR_SECRET
        
    async def extract_text_from_image(
        self,
        image_data: bytes,
        language: str = 'ko'
    ) -> Dict[str, Any]:
        """
        Extract text from food label image
        
        Args:
            image_data: Image bytes
            language: OCR language (ko, en, etc.)
            
        Returns:
            Dict containing extracted text and confidence scores
        """
        try:
            # Try CLOVA OCR first (optimized for Korean)
            if self.clova_secret and self.clova_url:
                result = await self._clova_ocr(image_data)
                if result:
                    return result
            
            # Fallback to Tesseract OCR
            logger.info("Using Tesseract OCR as fallback")
            result = await self._tesseract_ocr(image_data, language)
            return result
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {
                'success': False,
                'text': '',
                'error': str(e)
            }
    
    async def _clova_ocr(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        CLOVA OCR API call (Naver's Korean-optimized OCR)
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request
            request_json = {
                'images': [
                    {
                        'format': 'jpg',
                        'name': 'food_label',
                        'data': image_base64
                    }
                ],
                'requestId': 'fitmealor-ocr',
                'version': 'V2',
                'timestamp': 0
            }
            
            headers = {
                'X-OCR-SECRET': self.clova_secret,
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.clova_url,
                    json=request_json,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"CLOVA OCR error: {response.status_code}")
                    return None
                
                result = response.json()
                
                # Extract text from CLOVA response
                extracted_text = self._parse_clova_response(result)
                
                return {
                    'success': True,
                    'text': extracted_text['full_text'],
                    'structured_data': extracted_text['fields'],
                    'confidence': extracted_text['avg_confidence'],
                    'method': 'clova'
                }
                
        except Exception as e:
            logger.error(f"CLOVA OCR error: {e}")
            return None
    
    def _parse_clova_response(self, clova_result: Dict) -> Dict[str, Any]:
        """Parse CLOVA OCR response and extract structured data"""
        fields = []
        full_text = []
        confidences = []
        
        try:
            images = clova_result.get('images', [])
            if not images:
                return {'full_text': '', 'fields': [], 'avg_confidence': 0}
            
            for image in images:
                for field in image.get('fields', []):
                    text = field.get('inferText', '')
                    confidence = field.get('inferConfidence', 0)
                    
                    full_text.append(text)
                    confidences.append(confidence)
                    
                    fields.append({
                        'text': text,
                        'confidence': confidence,
                        'bounding_box': field.get('boundingPoly', {})
                    })
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'full_text': ' '.join(full_text),
                'fields': fields,
                'avg_confidence': avg_confidence
            }
            
        except Exception as e:
            logger.error(f"Error parsing CLOVA response: {e}")
            return {'full_text': '', 'fields': [], 'avg_confidence': 0}
    
    async def _tesseract_ocr(
        self,
        image_data: bytes,
        language: str = 'ko'
    ) -> Dict[str, Any]:
        """
        Tesseract OCR fallback
        Requires pytesseract installation
        """
        try:
            import pytesseract
            from PIL import Image
            
            # Load image
            image = Image.open(BytesIO(image_data))
            
            # Perform OCR with Korean language pack
            lang_code = 'kor' if language == 'ko' else 'eng'
            text = pytesseract.image_to_string(image, lang=lang_code)
            
            return {
                'success': True,
                'text': text.strip(),
                'structured_data': [],
                'confidence': 0.7,  # Estimated confidence
                'method': 'tesseract'
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return {
                'success': False,
                'text': '',
                'error': str(e)
            }
    
    async def detect_allergens_in_text(
        self,
        text: str,
        user_allergens: List[str],
        allergen_database: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect allergens in extracted text
        Supports Korean/English synonym matching
        
        Args:
            text: Extracted text from food label
            user_allergens: User's allergen list
            allergen_database: Database of allergen keywords
            
        Returns:
            Dict with detected allergens and warning level
        """
        detected_allergens = []
        warning_level = 'safe'
        
        # Normalize text
        text_lower = text.lower()
        
        for user_allergen in user_allergens:
            # Find matching allergen in database
            allergen_info = self._find_allergen_info(
                user_allergen,
                allergen_database
            )
            
            if not allergen_info:
                continue
            
            # Check for Korean keywords
            ko_keywords = allergen_info.get('keywords_ko', [])
            for keyword in ko_keywords:
                if keyword in text:
                    detected_allergens.append({
                        'allergen': allergen_info['name_en'],
                        'allergen_ko': allergen_info['name_ko'],
                        'matched_keyword': keyword,
                        'language': 'ko',
                        'severity': 'high'
                    })
                    warning_level = 'danger'
                    break
            
            # Check for English keywords
            en_keywords = allergen_info.get('keywords_en', [])
            for keyword in en_keywords:
                if keyword.lower() in text_lower:
                    detected_allergens.append({
                        'allergen': allergen_info['name_en'],
                        'allergen_ko': allergen_info['name_ko'],
                        'matched_keyword': keyword,
                        'language': 'en',
                        'severity': 'high'
                    })
                    warning_level = 'danger'
                    break
        
        # Check for common warning phrases
        if self._contains_warning_phrases(text):
            if warning_level != 'danger':
                warning_level = 'caution'
        
        return {
            'detected_allergens': detected_allergens,
            'warning_level': warning_level,
            'is_safe': len(detected_allergens) == 0,
            'total_detected': len(detected_allergens)
        }
    
    def _find_allergen_info(
        self,
        allergen_name: str,
        database: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find allergen information in database"""
        allergen_lower = allergen_name.lower()
        
        for item in database:
            # Check English name
            if item.get('name_en', '').lower() == allergen_lower:
                return item
            
            # Check Korean name
            if item.get('name_ko', '') == allergen_name:
                return item
            
            # Check keywords
            en_keywords = item.get('keywords_en', [])
            if any(kw.lower() == allergen_lower for kw in en_keywords):
                return item
            
            ko_keywords = item.get('keywords_ko', [])
            if allergen_name in ko_keywords:
                return item
        
        return None
    
    def _contains_warning_phrases(self, text: str) -> bool:
        """Check for common allergen warning phrases"""
        warning_phrases_ko = [
            '알레르기', '알러지', '주의', '함유', '포함',
            '유발', '성분', '민감', '반응'
        ]
        
        warning_phrases_en = [
            'allergen', 'allergy', 'contains', 'may contain',
            'warning', 'caution', 'sensitive'
        ]
        
        text_lower = text.lower()
        
        # Check Korean phrases
        if any(phrase in text for phrase in warning_phrases_ko):
            return True
        
        # Check English phrases
        if any(phrase in text_lower for phrase in warning_phrases_en):
            return True
        
        return False
    
    def extract_nutrition_info(self, text: str) -> Dict[str, Any]:
        """
        Extract nutrition information from OCR text
        Looks for common nutrition label patterns
        """
        nutrition_data = {}
        
        # Patterns for Korean nutrition labels
        patterns = {
            'calories': [
                r'열량[:\s]*(\d+)\s*kcal',
                r'칼로리[:\s]*(\d+)',
                r'(\d+)\s*칼로리'
            ],
            'protein': [
                r'단백질[:\s]*(\d+\.?\d*)\s*g',
                r'protein[:\s]*(\d+\.?\d*)\s*g'
            ],
            'carbs': [
                r'탄수화물[:\s]*(\d+\.?\d*)\s*g',
                r'carbohydrate[:\s]*(\d+\.?\d*)\s*g'
            ],
            'fat': [
                r'지방[:\s]*(\d+\.?\d*)\s*g',
                r'fat[:\s]*(\d+\.?\d*)\s*g'
            ],
            'sodium': [
                r'나트륨[:\s]*(\d+\.?\d*)\s*mg',
                r'sodium[:\s]*(\d+\.?\d*)\s*mg'
            ],
            'sugar': [
                r'당[:\s]*(\d+\.?\d*)\s*g',
                r'sugar[:\s]*(\d+\.?\d*)\s*g'
            ]
        }
        
        for nutrient, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        nutrition_data[nutrient] = float(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
        
        return nutrition_data

    async def extract_text_with_clova_ocr(
        self,
        image_data: bytes
    ) -> Dict[str, Any]:
        """
        Extract text from image using CLOVA OCR API

        Args:
            image_data: Image bytes

        Returns:
            Dict containing extracted text and OCR result
        """
        try:
            clova_api_url = os.getenv('CLOVA_OCR_URL',
                'https://p5xdnx3o9h.apigw.ntruss.com/custom/v1/47429/c26d84d5ff3819b6f84c6b97c58e38e8ee232b5fc5ee863bf1d3b6ce204602c3/infer')
            clova_api_key = os.getenv('CLOVA_OCR_SECRET',
                'alZuRUtubFVyQkFMRGpiT1lCeXhDZkRzV0poZ0pzclg=')

            if not clova_api_key:
                return {
                    'success': False,
                    'error': 'CLOVA OCR API key not configured'
                }

            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Prepare CLOVA OCR request
            import time
            import uuid

            request_json = {
                'version': 'V2',
                'requestId': str(uuid.uuid4()),
                'timestamp': int(time.time() * 1000),
                'images': [
                    {
                        'format': 'jpg',
                        'name': 'food_label',
                        'data': image_base64
                    }
                ]
            }

            headers = {
                'Content-Type': 'application/json',
                'X-OCR-SECRET': clova_api_key
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    clova_api_url,
                    json=request_json,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"CLOVA OCR API error: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'error': f'CLOVA OCR API error: {response.status_code}'
                    }

                result = response.json()

                # Extract text from OCR result
                extracted_text = []
                if 'images' in result and len(result['images']) > 0:
                    fields = result['images'][0].get('fields', [])
                    for field in fields:
                        text = field.get('inferText', '')
                        if text:
                            extracted_text.append(text)

                full_text = ' '.join(extracted_text)

                logger.info(f"CLOVA OCR extracted text length: {len(full_text)}")

                return {
                    'success': True,
                    'text': full_text,
                    'raw_result': result
                }

        except Exception as e:
            logger.error(f"CLOVA OCR error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def extract_structured_info_with_openai(
        self,
        image_data: bytes
    ) -> Dict[str, Any]:
        """
        Extract structured information from food label using OpenAI Vision API (GPT-4o)
        Directly analyzes image without intermediate OCR step

        Args:
            image_data: Image bytes

        Returns:
            Dict containing product_name, allergens, and nutrition_info
        """
        try:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not configured'
                }

            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Prepare OpenAI Vision API request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openai_api_key}'
            }

            prompt = """이 식품 라벨 이미지를 분석하여 다음 정보를 JSON 형식으로 추출해주세요:

추출할 정보:
1. product_name: 제품명 (한글과 영어 모두 있다면 한글 우선, 없으면 null)
2. allergens: 알러지 유발 성분 리스트 (예: ["땅콩", "우유", "대두"], 없으면 빈 배열)
3. nutrition_info: 영양 정보 객체 (다음 항목 포함)
   - calories: 칼로리 (kcal, 숫자만, 없으면 null)
   - carbohydrates: 탄수화물 (g, 숫자만, 없으면 null)
   - protein: 단백질 (g, 숫자만, 없으면 null)
   - fat: 지방 (g, 숫자만, 없으면 null)
   - sodium: 나트륨 (mg, 숫자만, 없으면 null)
   - sugar: 당류 (g, 숫자만, 없으면 null)

중요:
- 이미지에서 보이는 모든 텍스트를 주의 깊게 읽어주세요
- 영양성분표가 있다면 정확한 숫자를 추출해주세요
- 알러지 성분은 "알러지 유발 물질", "알레르기 유발 성분", "함유" 등의 섹션에서 찾아주세요
- 정보가 없는 항목은 null로 표시해주세요
- 응답은 반드시 순수 JSON 형식만 출력하고, 다른 텍스트는 포함하지 마세요

예시 형식:
{
  "product_name": "초코칩 쿠키",
  "allergens": ["밀", "우유", "대두"],
  "nutrition_info": {
    "calories": 520,
    "carbohydrates": 68.0,
    "protein": 6.5,
    "fat": 25.0,
    "sodium": 380,
    "sugar": 32.0
  }
}"""

            payload = {
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': prompt
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_base64}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 1000,
                'temperature': 0.2
            }

            logger.info("Sending image to OpenAI Vision API...")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"OpenAI Vision API error: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'error': f'OpenAI Vision API error: {response.status_code}'
                    }

                result = response.json()

                # Extract the response content
                content = result['choices'][0]['message']['content']

                logger.info(f"OpenAI Vision API response: {content[:200]}...")

                # Parse JSON from response
                try:
                    # Remove markdown code blocks if present
                    content = content.strip()
                    if content.startswith('```'):
                        # Remove ```json or ``` at start and ``` at end
                        content = content.split('\n', 1)[1] if '\n' in content else content
                        content = content.rsplit('```', 1)[0] if content.endswith('```') else content
                        content = content.strip()

                    extracted_data = json.loads(content)

                    logger.info(f"Successfully extracted data from image using OpenAI Vision")

                    return {
                        'success': True,
                        'product_name': extracted_data.get('product_name'),
                        'allergens': extracted_data.get('allergens', []),
                        'nutrition_info': extracted_data.get('nutrition_info', {})
                    }

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                    logger.error(f"Response content: {content}")
                    return {
                        'success': False,
                        'error': 'Failed to parse AI response',
                        'raw_response': content
                    }

        except Exception as e:
            logger.error(f"OpenAI Vision API error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global OCR service instance
ocr_service = FoodLabelOCRService()
