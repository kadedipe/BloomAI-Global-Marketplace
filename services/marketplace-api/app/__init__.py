from . import commerce
from .notifications import api_router

api_router.include_router(commerce.router)
