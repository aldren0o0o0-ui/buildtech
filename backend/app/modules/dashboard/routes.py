from app.core import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.dashboard.schemas import AdminDashboardResponse
from app.modules.dashboard.service import DashboardService
from app.modules.users.models import User

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


@router.get(
    "",
    response_model=AdminDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authoritative operational dashboard data",
)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Retrieves operational e-commerce dashboard metrics:
    - Paid revenue, pending payments, total orders, customers, and active products
    - Order counts partitioned across all lifecycle states
    - Real-time low-stock product warnings based on available quantity vs thresholds
    - Top-selling products based on completed sales volume
    - Most recent customer orders with payment and fulfillment status
    """
    return DashboardService.get_dashboard_data(db=db)
