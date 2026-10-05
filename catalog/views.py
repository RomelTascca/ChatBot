from django.db.models import Q
from django.shortcuts import render

from .models import Category, Offering, Product


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    current_category = request.GET.get("categoria", "").strip()
    query = request.GET.get("q", "").strip()

    if current_category:
        products = products.filter(category__slug=current_category)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    return render(request, "catalog/product_list.html", {
        "products": products,
        "categories": Category.objects.all(),
        "current_category": current_category,
        "query": query,
    })


KIND_TITLES = {
    Offering.Kind.SERVICE: "Servicios",
    Offering.Kind.BENEFIT: "Beneficios",
    Offering.Kind.PROMO: "Promociones",
    Offering.Kind.PLAN: "Planes",
    Offering.Kind.FEATURE: "Funcionalidades",
}


def offering_list(request):
    offerings = Offering.objects.filter(is_active=True)
    groups = {}
    for kind, title in KIND_TITLES.items():
        items = [o for o in offerings if o.kind == kind]
        if items:
            groups[title] = items
    return render(request, "catalog/offering_list.html", {"groups": groups})
