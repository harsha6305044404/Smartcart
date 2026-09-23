function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }

    return cookieValue;
}


async function sendAjaxRequest(url, method = "GET", data = null) {

    const options = {
        method: method,
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    };

    if (method !== "GET" && data) {
        options.headers["Content-Type"] = "application/json";
        options.headers["X-CSRFToken"] = getCookie("csrftoken");
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
        throw new Error("Request failed: " + response.status);
    }

    return await response.json();
}