from .notifications import api_router
from . import admin_refunds, commerce, hardening_routes, production_validation, support_assistant, support_cases
from . import hardening_compat as hardening_compat

_existing_routes = list(api_router.routes)
api_router.routes.clear()
api_router.include_router(hardening_routes.router)
api_router.include_router(production_validation.router)
api_router.include_router(admin_refunds.router)
api_router.include_router(support_assistant.router)
api_router.include_router(support_cases.router)
api_router.routes.extend(_existing_routes)
api_router.include_router(commerce.router)
