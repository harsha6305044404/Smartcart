from django.shortcuts import render, redirect, get_object_or_404
from .models import Order


def payment(request, order_id):
    if not request.user.is_authenticated:
        return redirect("login")

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if request.method == "POST":
        order.status = "Paid"
        order.save(update_fields=["status"])

        return redirect("payment_success", order_id=order.id)

    return render(
        request,
        "store/payment.html",
        {"order": order}
    )


def payment_success(request, order_id):
    if not request.user.is_authenticated:
        return redirect("login")

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "store/payment_success.html",
        {"order": order}
    )