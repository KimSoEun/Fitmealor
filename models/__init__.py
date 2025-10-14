from db.core import Base
#from .database import Base

# 반드시 실제 모델들을 import해서 Base.metadata에 등록되도록!
# from .user import User
# from .meal import Meal
# from .recommendation import Recommendation

# 필요한 모델 전부 import
# --- SQLAlchemy Base ---------------------------------------------------------
# --- SQLAlchemy Models -------------------------------------------------------
from .user import UserAccount
from .user import UserProfile
from .user import UserHealthMeasure
from .user import UserPreference
# --- Pydantic Schemas --------------------------------------------------------
from .user import ProfileBase
from .user import UserCreate
from .user import UserRead
from .user import UserProfileRead
from .user import UserHealthMeasureIn
from .user import UserHealthMeasureRead
from .user import UserPreferenceIn
from .user import UserPreferenceRead

# --- SQLAlchemy Base ---------------------------------------------------------
# --- Media (minimal) ---------------------------------------------------------
from .meal import ImageAsset
# --- Core Meal Models --------------------------------------------------------
from .meal import Meal
from .meal import MealI18n
from .meal import Ingredient
from .meal import MealIngredient
from .meal import Allergen
from .meal import IngredientAllergen
from .meal import Nutrient
from .meal import MealNutrient
from .meal import CuisineTag
from .meal import MealTag
# --- Pydantic Schemas --------------------------------------------------------
from .meal import MealCreate
from .meal import MealRead
from .meal import IngredientRead
from .meal import MealNutrientRead
from .meal import MealI18nIn

# --- SQLAlchemy Base ---------------------------------------------------------
from .recommendation import RecommendationSession
from .recommendation import RecommendationItem
from .recommendation import UserInteraction
from .recommendation import RatingFeedback
from .recommendation import AlgoFeatureSnapshot
# --- Pydantic Schemas --------------------------------------------------------
from .recommendation import RecoContext
from .recommendation import RecoRequest
from .recommendation import RecoItemDTO
from .recommendation import RecoResponse
from .recommendation import InteractionIn
from .recommendation import FeedbackIn
