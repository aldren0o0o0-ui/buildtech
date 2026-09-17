from app.core import APIRouter

from app.modules.addresses.routes import router as addresses_router

from app.modules.auth.routes import router as auth_router
from app.modules.carts.routes import router as cart_router
from app.modules.catalog.brand_routes import router as brands_router
from app.modules.catalog.category_routes import router as categories_router
from app.modules.checkout.routes import router as checkout_validation_router
from app.modules.inventory.routes import (
    inventory_router,
    public_availability_router,
)
from app.modules.orders.routes import (
    admin_orders_router,
    checkout_router,
    customer_orders_router,
)
from app.modules.payment.routes import (
    admin_payments_router,
    customer_payments_router,
)
from app.modules.products.routes import router as products_router
from app.modules.products.specifications.routes import router as specifications_router
from app.modules.reviews.routes import (
    admin_reviews_router,
    product_reviews_router,
    reviews_router,
)
from app.modules.dashboard.routes import router as admin_dashboard_router
from app.modules.users.routes import router as users_router
from app.modules.wishlist.routes import router as wishlist_router
from app.modules.compatibility.routes import router as compatibility_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(addresses_router)
api_router.include_router(categories_router)
api_router.include_router(brands_router)
api_router.include_router(products_router)
api_router.include_router(specifications_router)
api_router.include_router(inventory_router)
api_router.include_router(public_availability_router)
api_router.include_router(cart_router)
api_router.include_router(wishlist_router)
api_router.include_router(checkout_validation_router)
api_router.include_router(checkout_router)
api_router.include_router(customer_orders_router)
api_router.include_router(admin_orders_router)
api_router.include_router(customer_payments_router)
api_router.include_router(admin_payments_router)
api_router.include_router(product_reviews_router)
api_router.include_router(reviews_router)
api_router.include_router(admin_reviews_router)
api_router.include_router(admin_dashboard_router)
api_router.include_router(compatibility_router)


