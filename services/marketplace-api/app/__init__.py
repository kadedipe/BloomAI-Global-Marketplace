from .notifications import api_router
from . import commerce, hardening, hardening_compat

_existing_routes = list(api_router.routes)
api_router.routes.clear()
api_router.include_router(hardening.router)
api_router.routes.extend(_existing_routes)
api_router.include_router(commerce.router)
