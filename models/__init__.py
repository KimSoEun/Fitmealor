from db.core import Base

# 반드시 실제 모델들을 import해서 Base.metadata에 등록되도록!
from .user import User
from .meal import Meal
from .recommendation import Recommendation
# 필요한 모델 전부 import

