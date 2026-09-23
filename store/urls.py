from django.urls import path
from . import views
from . import api_views
from . import payment

urlpatterns = [
    path("", views.home, name="home"),

    path(
        "product/<int:product_id>/",
        views.product_detail,
        name="product_detail"
    ),

    path(
        "product/<int:product_id>/review/",
        views.add_review,
        name="add_review"
    ),

    path(
        "add-to-cart/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "increase/<int:product_id>/",
        views.increase_quantity,
        name="increase_quantity"
    ),

    path(
        "decrease/<int:product_id>/",
        views.decrease_quantity,
        name="decrease_quantity"
    ),

    path(
        "remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),

    path("cart/", views.cart, name="cart"),

    path("checkout/", views.checkout, name="checkout"),

    path(
        "order-success/",
        views.order_success,
        name="order_success"
    ),

    path(
        "orders/",
        views.my_orders,
        name="my_orders"
    ),

    path(
        "orders/<int:order_id>/",
        views.order_detail,
        name="order_detail"
    ),

    path(
        "wishlist/",
        views.wishlist,
        name="wishlist"
    ),

    path(
        "wishlist/add/<int:product_id>/",
        views.add_to_wishlist,
        name="add_to_wishlist"
    ),

    path(
        "wishlist/remove/<int:product_id>/",
        views.remove_from_wishlist,
        name="remove_from_wishlist"
    ),

    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path("register/", views.register, name="register"),

    path("login/", views.login_user, name="login"),

    path("logout/", views.logout_user, name="logout"),

    # REST API
    path(
        "api/products/",
        api_views.ProductListAPIView.as_view(),
        name="api_products"
    ),

    path(
        "api/products/<int:pk>/",
        api_views.ProductDetailAPIView.as_view(),
        name="api_product_detail"
    ),

    path(
        "api/products/<int:product_id>/reviews/",
        api_views.ReviewListCreateAPIView.as_view(),
        name="api_product_reviews"
    ),

    # Mock Payment
    path(
        "payment/<int:order_id>/",
        payment.payment,
        name="payment"
    ),

    path(
        "payment-success/<int:order_id>/",
        payment.payment_success,
        name="payment_success"
    ),
]