from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Product


def get_recommendations(product_id, limit=4):
    products = list(Product.objects.all())

    if len(products) <= 1:
        return []

    selected_product = next(
        (
            product
            for product in products
            if product.id == product_id
        ),
        None
    )

    if selected_product is None:
        return []

    documents = []

    for product in products:
        text = (
            f"category {product.category} "
            f"category {product.category} "
            f"category {product.category} "
            f"name {product.name} "
            f"description {product.description}"
        )

        documents.append(text)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        lowercase=True
    )

    matrix = vectorizer.fit_transform(documents)

    selected_index = products.index(selected_product)

    similarity_scores = cosine_similarity(
        matrix[selected_index],
        matrix
    ).flatten()

    ranked_indexes = similarity_scores.argsort()[::-1]

    recommendations = []

    for index in ranked_indexes:
        if index == selected_index:
            continue

        recommendations.append(products[index])

        if len(recommendations) >= limit:
            break

    return recommendations