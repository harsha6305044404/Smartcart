from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction, models
from django.db.models import Sum
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Product, Order, OrderItem, Wishlist, Review
from .recommendations import get_recommendations


def home(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "").strip()

    products = Product.objects.all()

    if query:
        products = products.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(category__icontains=query)
        )

    if category:
        products = products.filter(category__iexact=category)

    if sort == "price_low":
        products = products.order_by("price")
    elif sort == "price_high":
        products = products.order_by("-price")
    else:
        products = products.order_by("-created_at")

    categories = Product.objects.values_list(
        "category",
        flat=True
    ).distinct().order_by("category")

    return render(
        request,
        "store/home.html",
        {
            "products": products,
            "query": query,
            "category": category,
            "sort": sort,
            "categories": categories,
        },
    )


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    reviews = product.reviews.select_related("user").all()
    review_count = reviews.count()

    if review_count:
        average_rating = sum(
            review.rating for review in reviews
        ) / review_count
    else:
        average_rating = 0

    user_review = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            user=request.user,
            product=product
        ).first()

    recommendations = get_recommendations(
        product.id,
        limit=4
    )

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "average_rating": average_rating,
            "review_count": review_count,
            "user_review": user_review,
            "recommendations": recommendations,
        },
    )


def add_review(request, product_id):
    if not request.user.is_authenticated:
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = 0

        if 1 <= rating <= 5 and comment:
            Review.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={
                    "rating": rating,
                    "comment": comment,
                },
            )

    return redirect("product_detail", product_id=product.id)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    key = str(product_id)
    current_quantity = cart.get(key, 0)

    if current_quantity < product.stock:
        cart[key] = current_quantity + 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def increase_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    key = str(product_id)
    current_quantity = cart.get(key, 0)

    if current_quantity < product.stock:
        cart[key] = current_quantity + 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def decrease_quantity(request, product_id):
    cart = request.session.get("cart", {})
    key = str(product_id)

    if key in cart:
        cart[key] -= 1

        if cart[key] <= 0:
            del cart[key]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    key = str(product_id)

    if key in cart:
        del cart[key]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def cart(request):
    cart_data = request.session.get("cart", {})

    products = []
    total = 0

    for product_id, quantity in cart_data.items():
        product = get_object_or_404(
            Product,
            id=int(product_id)
        )

        item_total = product.price * quantity
        total += item_total

        products.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

    return render(
        request,
        "store/cart.html",
        {
            "products": products,
            "total": total,
        },
    )


def checkout(request):
    cart_data = request.session.get("cart", {})

    products = []
    total = 0
    errors = []

    for product_id, quantity in cart_data.items():
        product = get_object_or_404(
            Product,
            id=int(product_id)
        )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        if quantity > product.stock:
            errors.append(
                f"{product.name} has only {product.stock} item(s) available."
            )
            continue

        item_total = product.price * quantity
        total += item_total

        products.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

    if errors:
        return render(
            request,
            "store/checkout.html",
            {
                "products": products,
                "total": total,
                "error": " ".join(errors),
            },
        )

    if not products:
        return redirect("cart")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        if not name or not email or not phone or not address:
            return render(
                request,
                "store/checkout.html",
                {
                    "products": products,
                    "total": total,
                    "error": "Please fill in all delivery details.",
                },
            )

        try:
            validate_email(email)
        except ValidationError:
            return render(
                request,
                "store/checkout.html",
                {
                    "products": products,
                    "total": total,
                    "error": "Please enter a valid email address.",
                },
            )

        phone_digits = "".join(
            character for character in phone
            if character.isdigit()
        )

        if len(phone_digits) < 10 or len(phone_digits) > 15:
            return render(
                request,
                "store/checkout.html",
                {
                    "products": products,
                    "total": total,
                    "error": "Please enter a valid phone number.",
                },
            )

        with transaction.atomic():
            for item in products:
                product = Product.objects.select_for_update().get(
                    id=item["product"].id
                )

                if item["quantity"] > product.stock:
                    return render(
                        request,
                        "store/checkout.html",
                        {
                            "products": products,
                            "total": total,
                            "error": (
                                f"{product.name} is no longer available "
                                f"in the requested quantity."
                            ),
                        },
                    )

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                phone=phone,
                address=address,
                total_amount=total,
                status="Placed",
            )

            for item in products:
                product = Product.objects.select_for_update().get(
                    id=item["product"].id
                )

                quantity = item["quantity"]

                product.stock -= quantity
                product.save(update_fields=["stock"])

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )

        request.session["cart"] = {}
        request.session["last_order_id"] = order.id
        request.session.modified = True

        if request.user.is_authenticated:
            return redirect("payment", order_id=order.id)

        return redirect("order_success")

    return render(
        request,
        "store/checkout.html",
        {
            "products": products,
            "total": total,
        },
    )


def order_success(request):
    order_id = request.session.get("last_order_id")

    if not order_id:
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)

    return render(
        request,
        "store/order_success.html",
        {"order": order},
    )


def order_detail(request, order_id):
    if not request.user.is_authenticated:
        return redirect("login")

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "store/order_detail.html",
        {"order": order},
    )


def my_orders(request):
    if not request.user.is_authenticated:
        return redirect("login")

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "store/my_orders.html",
        {"orders": orders},
    )


def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect("wishlist")


def remove_from_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect("login")

    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    return redirect("wishlist")


def wishlist(request):
    if not request.user.is_authenticated:
        return redirect("login")

    items = Wishlist.objects.filter(
        user=request.user
    ).select_related("product").order_by("-created_at")

    return render(
        request,
        "store/wishlist.html",
        {"items": items},
    )


def profile(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user = request.user
    message = ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        message = "Profile updated successfully."

    return render(
        request,
        "store/profile.html",
        {
            "profile_user": user,
            "message": message,
        },
    )


@staff_member_required(login_url="/login/")
def dashboard(request):
    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    total_customers = User.objects.filter(
        is_staff=False
    ).count()

    revenue = Order.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    recent_orders = Order.objects.select_related(
        "user"
    ).order_by("-created_at")[:10]

    low_stock_products = Product.objects.filter(
        stock__lte=5
    ).order_by("stock")

    context = {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "revenue": revenue,
        "recent_orders": recent_orders,
        "low_stock_products": low_stock_products,
    }

    return render(
        request,
        "store/dashboard.html",
        context,
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request,
                "store/register.html",
                {"error": "Passwords do not match."},
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "store/register.html",
                {"error": "Username already exists."},
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        login(request, user)

        return redirect("home")

    return render(request, "store/register.html")


def login_user(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(
            request,
            "store/login.html",
            {"error": "Invalid username or password."},
        )

    return render(request, "store/login.html")


def logout_user(request):
    logout(request)
    return redirect("home")
def custom_404(request, exception):
    return render(
        request,
        "404.html",
        status=404
    )
