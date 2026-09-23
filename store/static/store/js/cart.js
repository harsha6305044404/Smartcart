document.addEventListener("DOMContentLoaded", function () {

    const buttons = document.querySelectorAll("[data-cart-action]");

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            if (button.disabled) {
                return;
            }

            button.disabled = true;

            const originalText = button.innerText;
            button.innerText = "Updating...";

            const url = button.getAttribute("data-url");

            if (url) {
                window.location.href = url;
            } else {
                button.disabled = false;
                button.innerText = originalText;
            }

        });

    });

});