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


# Global OCR service instance
ocr_service = FoodLabelOCRService()
