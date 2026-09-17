from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.products.models import Product, ProductStatus
from app.modules.reviews.models import Review, ReviewStatus
from app.modules.users.models import User, UserRole


@pytest.fixture
def test_category(db_session):
    cat = Category(name="Components", slug="components", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def test_brand(db_session):
    brand = Brand(name="AMD", slug="amd", is_active=True)
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def test_product(db_session, test_category, test_brand):
    prod = Product(
        sku="CPU-RYZEN-7800X3D",
        name="AMD Ryzen 7 7800X3D",
        slug="amd-ryzen-7-7800x3d",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("449.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod


@pytest.fixture
def second_product(db_session, test_category, test_brand):
    prod = Product(
        sku="GPU-RADEON-7900XTX",
        name="AMD Radeon RX 7900 XTX",
        slug="amd-radeon-rx-7900-xtx",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("899.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod


@pytest.fixture
def second_customer(db_session):
    user = User(
        email="second_customer@example.com",
        password_hash=hash_password("Password123!"),
        first_name="Bob",
        last_name="Smith",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def customer_auth_headers(test_customer_user):
    token = create_access_token(
        subject=test_customer_user.id,
        role=test_customer_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_customer_auth_headers(second_customer):
    token = create_access_token(
        subject=second_customer.id,
        role=second_customer.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user):
    token = create_access_token(
        subject=test_admin_user.id,
        role=test_admin_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


def create_customer_order(db_session, user_id, product, order_status=OrderStatus.CONFIRMED.value):
    order = Order(
        order_number=f"BT-TEST-{user_id}-{product.id}-{order_status[:3]}",
        user_id=user_id,
        status=order_status,
        payment_method="CASH_ON_DELIVERY",
        payment_status="PENDING",
        subtotal=product.price,
        shipping_fee=Decimal("0.00"),
        total_amount=product.price,
        customer_name="Test Customer",
        customer_email="customer@example.com",
        customer_phone="+639170000000",
        shipping_address_line1="123 Street",
        shipping_city="Pasig",
        shipping_province="Metro Manila",
        shipping_postal_code="1600",
    )
    db_session.add(order)
    db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        product_sku=product.sku,
        product_slug=product.slug,
        unit_price=product.price,
        quantity=1,
        subtotal=product.price,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(order)
    return order


# ===========================================================================
# 1. Authentication & Guest Protection
# ===========================================================================

def test_guest_cannot_create_review(client, test_product):
    payload = {"rating": 5, "title": "Great CPU", "comment": "Excellent gaming performance!"}
    res = client.post(f"/api/v1/products/{test_product.id}/reviews", json=payload)
    assert res.status_code == 401


def test_guest_cannot_update_review(client):
    res = client.patch("/api/v1/reviews/1", json={"rating": 4})
    assert res.status_code == 401


def test_guest_cannot_delete_review(client):
    res = client.delete("/api/v1/reviews/1")
    assert res.status_code == 401


# ===========================================================================
# 2. Purchase Verification & Eligibility
# ===========================================================================

def test_verified_purchaser_can_create_review(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    payload = {
        "rating": 5,
        "title": "Unbelievable Gaming Speeds",
        "comment": "Runs cool with my AIO and frame rates are buttery smooth.",
    }
    res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json=payload,
        headers=customer_auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["rating"] == 5
    assert data["title"] == "Unbelievable Gaming Speeds"
    assert data["is_verified_purchase"] is True
    assert data["author_name"] == "Jane D."

    # Check database persistence
    review = db_session.query(Review).filter(Review.id == data["id"]).first()
    assert review is not None
    assert review.user_id == test_customer_user.id
    assert review.product_id == test_product.id
    assert review.status == "PUBLISHED"


def test_non_purchaser_cannot_create_review(
    client, test_customer_user, test_product, customer_auth_headers
):
    # Customer has NOT ordered test_product
    payload = {
        "rating": 4,
        "title": "Looks good on paper",
        "comment": "I haven't bought it yet but it seems great.",
    }
    res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json=payload,
        headers=customer_auth_headers,
    )
    assert res.status_code == 403
    assert "verified purchasers" in res.json()["detail"].lower()


def test_cancelled_order_does_not_grant_review_eligibility(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    # Order was CANCELLED
    create_customer_order(
        db_session, test_customer_user.id, test_product, order_status=OrderStatus.CANCELLED.value
    )

    payload = {
        "rating": 1,
        "title": "Cancelled my order",
        "comment": "Never arrived because I cancelled it.",
    }
    res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json=payload,
        headers=customer_auth_headers,
    )
    assert res.status_code == 403
    assert "verified purchasers" in res.json()["detail"].lower()


# ===========================================================================
# 3. Uniqueness & Duplicate Review Prevention
# ===========================================================================

def test_one_review_per_product_enforced(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    payload1 = {"rating": 5, "title": "First Review", "comment": "Excellent component."}
    res1 = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json=payload1,
        headers=customer_auth_headers,
    )
    assert res1.status_code == 201

    # Second review attempt for the same product by the same customer
    payload2 = {"rating": 4, "title": "Second Review", "comment": "Still good."}
    res2 = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json=payload2,
        headers=customer_auth_headers,
    )
    assert res2.status_code == 409
    assert "already submitted a review" in res2.json()["detail"].lower()


def test_database_uniqueness_constraint_enforced(db_session, test_customer_user, test_product):
    rev1 = Review(
        user_id=test_customer_user.id,
        product_id=test_product.id,
        rating=5,
        title="Direct Review 1",
        comment="Comment 1",
        is_verified_purchase=True,
    )
    db_session.add(rev1)
    db_session.commit()

    rev2 = Review(
        user_id=test_customer_user.id,
        product_id=test_product.id,
        rating=4,
        title="Direct Review 2",
        comment="Comment 2",
        is_verified_purchase=True,
    )
    db_session.add(rev2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ===========================================================================
# 4. Rating Constraints & Payload Validation
# ===========================================================================

def test_rating_range_validation(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    # 0 star -> rejected
    res_zero = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 0, "title": "Too low", "comment": "Zero stars"},
        headers=customer_auth_headers,
    )
    assert res_zero.status_code == 422

    # 6 star -> rejected
    res_six = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 6, "title": "Too high", "comment": "Six stars"},
        headers=customer_auth_headers,
    )
    assert res_six.status_code == 422

    # Title too short -> rejected
    res_short = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "A", "comment": "Short title"},
        headers=customer_auth_headers,
    )
    assert res_short.status_code == 422


# ===========================================================================
# 5. Customer Ownership Isolation (Edit & Delete)
# ===========================================================================

def test_customer_can_edit_own_review(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 4, "title": "Initial Title", "comment": "Initial comment text."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    # Customer updates review
    patch_res = client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"rating": 5, "title": "Updated Title: Even Better!", "comment": "Updated comment after overclocking."},
        headers=customer_auth_headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["rating"] == 5
    assert data["title"] == "Updated Title: Even Better!"
    assert data["comment"] == "Updated comment after overclocking."


def test_customer_cannot_edit_another_customer_review(
    client,
    db_session,
    test_customer_user,
    second_customer,
    test_product,
    customer_auth_headers,
    second_customer_auth_headers,
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    # Customer 1 writes review
    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "Jane's Review", "comment": "Great CPU."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    # Customer 2 attempts to edit Customer 1's review
    patch_res = client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"rating": 1, "title": "Hacked Title", "comment": "Tampered comment."},
        headers=second_customer_auth_headers,
    )
    assert patch_res.status_code == 404
    assert "not found" in patch_res.json()["detail"].lower()


def test_customer_can_delete_own_review(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "To Delete", "comment": "Will be deleted."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    del_res = client.delete(f"/api/v1/reviews/{review_id}", headers=customer_auth_headers)
    assert del_res.status_code == 204

    # Verify removed from database
    assert db_session.query(Review).filter(Review.id == review_id).first() is None


def test_customer_cannot_delete_another_customer_review(
    client,
    db_session,
    test_customer_user,
    second_customer,
    test_product,
    customer_auth_headers,
    second_customer_auth_headers,
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "Jane's Review", "comment": "Cannot delete me."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    # Customer 2 attempts to delete Customer 1's review
    del_res = client.delete(f"/api/v1/reviews/{review_id}", headers=second_customer_auth_headers)
    assert del_res.status_code == 404

    # Verify review still exists
    assert db_session.query(Review).filter(Review.id == review_id).first() is not None


# ===========================================================================
# 6. SQL Aggregations & Public Storefront Presentation
# ===========================================================================

def test_public_reviews_list_and_summary(
    client,
    db_session,
    test_customer_user,
    second_customer,
    test_product,
    customer_auth_headers,
    second_customer_auth_headers,
):
    create_customer_order(db_session, test_customer_user.id, test_product)
    create_customer_order(db_session, second_customer.id, test_product)

    # Customer 1: 5 stars
    client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "Five stars", "comment": "Five stars review"},
        headers=customer_auth_headers,
    )
    # Customer 2: 3 stars
    client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 3, "title": "Three stars", "comment": "Three stars review"},
        headers=second_customer_auth_headers,
    )

    # Public list endpoint
    list_res = client.get(f"/api/v1/products/{test_product.id}/reviews")
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Check SQL Aggregations: Average = (5 + 3) / 2 = 4.0
    summary = data["summary"]
    assert summary["total_reviews"] == 2
    assert summary["average_rating"] == 4.0
    assert summary["rating_distribution"]["5"] == 1
    assert summary["rating_distribution"]["3"] == 1
    assert summary["rating_distribution"]["4"] == 0

    # Summary standalone endpoint
    sum_res = client.get(f"/api/v1/products/{test_product.id}/reviews/summary")
    assert sum_res.status_code == 200
    assert sum_res.json()["average_rating"] == 4.0


# ===========================================================================
# 7. Admin Moderation (Hide/Publish) & Public Visibility
# ===========================================================================

def test_admin_can_hide_and_publish_review(
    client,
    db_session,
    test_customer_user,
    test_product,
    customer_auth_headers,
    admin_auth_headers,
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 1, "title": "Inappropriate", "comment": "Rude and offensive comment."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    # Admin hides the review
    hide_res = client.patch(
        f"/api/v1/admin/reviews/{review_id}/status",
        json={"status": "HIDDEN"},
        headers=admin_auth_headers,
    )
    assert hide_res.status_code == 200
    assert hide_res.json()["status"] == "HIDDEN"

    # Verify public storefront does NOT display hidden review
    pub_res = client.get(f"/api/v1/products/{test_product.id}/reviews")
    assert pub_res.json()["total"] == 0
    assert pub_res.json()["summary"]["total_reviews"] == 0

    # Admin publishes review again
    pub_action = client.patch(
        f"/api/v1/admin/reviews/{review_id}/status",
        json={"status": "PUBLISHED"},
        headers=admin_auth_headers,
    )
    assert pub_action.status_code == 200
    assert pub_action.json()["status"] == "PUBLISHED"

    # Verify public storefront now displays the review
    pub_res2 = client.get(f"/api/v1/products/{test_product.id}/reviews")
    assert pub_res2.json()["total"] == 1
    assert pub_res2.json()["summary"]["total_reviews"] == 1


def test_customer_cannot_moderate_review(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "Great", "comment": "Great component."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    # Customer tries to hide review via admin endpoint
    res = client.patch(
        f"/api/v1/admin/reviews/{review_id}/status",
        json={"status": "HIDDEN"},
        headers=customer_auth_headers,
    )
    assert res.status_code == 403


# ===========================================================================
# 8. Admin Review Listing, Search, and Inspection
# ===========================================================================

def test_admin_list_and_search_reviews(
    client, db_session, test_customer_user, test_product, customer_auth_headers, admin_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "KeywordAlpha", "comment": "ContentOmega"},
        headers=customer_auth_headers,
    )

    # Admin lists all reviews
    list_res = client.get("/api/v1/admin/reviews", headers=admin_auth_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1

    first = data["items"][0]
    assert "user_email" in first
    assert "product_name" in first
    assert "status" in first

    # Test search by title keyword
    search_res = client.get("/api/v1/admin/reviews?search=KeywordAlpha", headers=admin_auth_headers)
    assert search_res.status_code == 200
    assert any(item["title"] == "KeywordAlpha" for item in search_res.json()["items"])


def test_admin_delete_review(
    client, db_session, test_customer_user, test_product, customer_auth_headers, admin_auth_headers
):
    create_customer_order(db_session, test_customer_user.id, test_product)

    post_res = client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 1, "title": "Spam", "comment": "Spam comment."},
        headers=customer_auth_headers,
    )
    review_id = post_res.json()["id"]

    del_res = client.delete(f"/api/v1/admin/reviews/{review_id}", headers=admin_auth_headers)
    assert del_res.status_code == 204
    assert db_session.query(Review).filter(Review.id == review_id).first() is None


# ===========================================================================
# 9. Review Sorting & Customer My-Review Status
# ===========================================================================

def test_review_sorting(
    client,
    db_session,
    test_customer_user,
    second_customer,
    test_product,
    customer_auth_headers,
    second_customer_auth_headers,
):
    create_customer_order(db_session, test_customer_user.id, test_product)
    create_customer_order(db_session, second_customer.id, test_product)

    # Low rating
    client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 2, "title": "Low rating", "comment": "Two stars."},
        headers=customer_auth_headers,
    )
    # High rating
    client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "High rating", "comment": "Five stars."},
        headers=second_customer_auth_headers,
    )

    # Highest rating sort
    high_res = client.get(f"/api/v1/products/{test_product.id}/reviews?sort_by=highest_rating")
    assert high_res.status_code == 200
    assert high_res.json()["items"][0]["rating"] == 5

    # Lowest rating sort
    low_res = client.get(f"/api/v1/products/{test_product.id}/reviews?sort_by=lowest_rating")
    assert low_res.status_code == 200
    assert low_res.json()["items"][0]["rating"] == 2


def test_get_my_review_status(
    client, db_session, test_customer_user, test_product, customer_auth_headers
):
    # Case 1: Has not purchased -> cannot review
    me_res1 = client.get(f"/api/v1/products/{test_product.id}/reviews/me", headers=customer_auth_headers)
    assert me_res1.status_code == 200
    assert me_res1.json()["can_review"] is False
    assert me_res1.json()["has_reviewed"] is False

    # Case 2: Purchases -> can review
    create_customer_order(db_session, test_customer_user.id, test_product)
    me_res2 = client.get(f"/api/v1/products/{test_product.id}/reviews/me", headers=customer_auth_headers)
    assert me_res2.status_code == 200
    assert me_res2.json()["can_review"] is True
    assert me_res2.json()["has_reviewed"] is False

    # Case 3: Reviews product -> has reviewed
    client.post(
        f"/api/v1/products/{test_product.id}/reviews",
        json={"rating": 5, "title": "My Review", "comment": "Comment here."},
        headers=customer_auth_headers,
    )
    me_res3 = client.get(f"/api/v1/products/{test_product.id}/reviews/me", headers=customer_auth_headers)
    assert me_res3.status_code == 200
    assert me_res3.json()["can_review"] is False
    assert me_res3.json()["has_reviewed"] is True
    assert me_res3.json()["review"]["title"] == "My Review"
