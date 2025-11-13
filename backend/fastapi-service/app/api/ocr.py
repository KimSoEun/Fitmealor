"""
OCR API endpoints for food label scanning
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AllergenDetectionRequest(BaseModel):
    text: str
    user_allergens: List[str]
    language: str = 'ko'


@router.post("/scan")
async def scan_food_label(
    file: UploadFile = File(...),
    language: str = 'ko'
):
    """
    Scan food label image and extract text
    Optimized for Korean food labels
    
    Args:
        file: Image file (JPG, PNG)
        language: OCR language (ko, en, zh, ja)
    
    Returns:
        Extracted text and nutritional information
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Perform OCR
        ocr_result = await ocr_service.extract_text_from_image(
            image_data,
            language=language
        )
        
        if not ocr_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=ocr_result.get('error', 'OCR failed')
            )
        
        # Extract nutrition information
        nutrition_info = ocr_service.extract_nutrition_info(
            ocr_result['text']
        )
        
        return {
            "success": True,
            "extracted_text": ocr_result['text'],
            "confidence": ocr_result.get('confidence', 0),
            "method": ocr_result.get('method', 'unknown'),
            "nutrition_info": nutrition_info,
            "structured_data": ocr_result.get('structured_data', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning food label: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-allergens")
async def detect_allergens(request: AllergenDetectionRequest):
    """
    Detect allergens in extracted text
    Supports Korean/English keyword matching
    
    Args:
        text: Extracted text from food label
        user_allergens: User's allergen list
        language: Text language
    
    Returns:
        Detected allergens and warning level
    """
    try:
        # Mock allergen database (would come from PostgreSQL in production)
        allergen_database = [
            {
                'name_en': 'Peanuts',
                'name_ko': '땅콩',
                'keywords_en': ['peanut', 'groundnut'],
                'keywords_ko': ['땅콩', '낙화생']
            },
            {
                'name_en': 'Milk',
                'name_ko': '우유',
                'keywords_en': ['milk', 'dairy', 'lactose'],
                'keywords_ko': ['우유', '유제품', '유당']
            },
            {
                'name_en': 'Eggs',
                'name_ko': '계란',
                'keywords_en': ['egg', 'albumin'],
                'keywords_ko': ['계란', '달걀', '난류']
            },
            {
                'name_en': 'Soy',
                'name_ko': '콩',
                'keywords_en': ['soy', 'soybean'],
                'keywords_ko': ['콩', '대두']
            },
            {
                'name_en': 'Wheat',
                'name_ko': '밀',
                'keywords_en': ['wheat', 'gluten'],
                'keywords_ko': ['밀', '밀가루', '글루텐']
            },
            {
                'name_en': 'Shellfish',
                'name_ko': '갑각류',
                'keywords_en': ['shrimp', 'crab', 'lobster'],
                'keywords_ko': ['새우', '게', '랍스터']
            }
        ]
        
        # Detect allergens
        detection_result = await ocr_service.detect_allergens_in_text(
            request.text,
            request.user_allergens,
            allergen_database
        )
        
        return {
            "success": True,
            "detection_result": detection_result,
            "user_allergens": request.user_allergens,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error detecting allergens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-and-detect")
async def scan_and_detect_allergens(
    file: UploadFile = File(...),
    user_allergens: str = '',  # Comma-separated list
    language: str = 'ko'
):
    """
    Complete workflow: Scan food label and detect allergens

    Args:
        file: Image file
        user_allergens: Comma-separated allergen list
        language: OCR language

    Returns:
        OCR text, nutrition info, and allergen warnings
    """
    try:
        # Parse user allergens
        allergen_list = [a.strip() for a in user_allergens.split(',') if a.strip()]

        # Scan image
        image_data = await file.read()
        ocr_result = await ocr_service.extract_text_from_image(
            image_data,
            language=language
        )

        if not ocr_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="OCR failed"
            )

        # Extract nutrition
        nutrition_info = ocr_service.extract_nutrition_info(
            ocr_result['text']
        )

        # Detect allergens
        allergen_database = [
            {
                'name_en': 'Peanuts', 'name_ko': '땅콩',
                'keywords_en': ['peanut'], 'keywords_ko': ['땅콩']
            },
            {
                'name_en': 'Milk', 'name_ko': '우유',
                'keywords_en': ['milk', 'dairy'], 'keywords_ko': ['우유', '유제품']
            },
            {
                'name_en': 'Eggs', 'name_ko': '계란',
                'keywords_en': ['egg'], 'keywords_ko': ['계란', '달걀']
            }
        ]

        allergen_detection = await ocr_service.detect_allergens_in_text(
            ocr_result['text'],
            allergen_list,
            allergen_database
        )

        return {
            "success": True,
            "extracted_text": ocr_result['text'],
            "confidence": ocr_result.get('confidence', 0),
            "nutrition_info": nutrition_info,
            "allergen_detection": allergen_detection,
            "warning_level": allergen_detection['warning_level'],
            "is_safe": allergen_detection['is_safe']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in scan and detect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-with-ai")
async def analyze_food_label_with_ai(
    file: UploadFile = File(...)
):
    """
    Analyze food label using OpenAI Vision API
    Extracts: product name, allergens, and nutrition information

    Args:
        file: Image file (JPG, PNG, HEIC)

    Returns:
        Structured data with product_name, allergens, and nutrition_info
    """
    try:
        # Validate file type (be permissive to support various upload methods)
        if file.content_type:
            # Only reject if content_type is explicitly NOT an image
            if not file.content_type.startswith('image/') and file.content_type != 'application/octet-stream':
                raise HTTPException(
                    status_code=400,
                    detail="File must be an image"
                )

        # Read image data
        image_data = await file.read()

        # Verify it's actually an image and convert HEIC to JPEG if needed
        try:
            from PIL import Image
            from io import BytesIO
            import pillow_heif

            # Register HEIC opener with PIL
            pillow_heif.register_heif_opener()

            # Open and verify image
            img = Image.open(BytesIO(image_data))

            # Convert HEIC to JPEG for OpenAI API compatibility
            # (OpenAI Vision API works best with JPEG/PNG)
            if img.format == 'HEIF' or file.filename.lower().endswith('.heic'):
                logger.info("Converting HEIC image to JPEG")
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                # Save as JPEG in memory
                output = BytesIO()
                img.save(output, format='JPEG', quality=95)
                image_data = output.getvalue()
                logger.info("HEIC conversion successful")

        except Exception as e:
            logger.error(f"Image validation error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )

        # Extract structured information using OpenAI Vision API
        result = await ocr_service.extract_structured_info_with_openai(image_data)

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'AI analysis failed')
            )

        return {
            "success": True,
            "product_name": result.get('product_name'),
            "allergens": result.get('allergens', []),
            "nutrition_info": result.get('nutrition_info', {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing food label with AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))
