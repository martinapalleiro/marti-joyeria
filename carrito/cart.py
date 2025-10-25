# carrito/cart.py
from decimal import Decimal
from .models import Producto

class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(self.SESSION_KEY, {})
        if self.SESSION_KEY not in self.session:
            self.session[self.SESSION_KEY] = self.cart

    def add(self, product_id, quantity=1, override=False):
        pid = str(product_id)
        if pid not in self.cart:
            self.cart[pid] = {"qty": 0}
        self.cart[pid]["qty"] = quantity if override else self.cart[pid]["qty"] + quantity
        self.save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session[self.SESSION_KEY] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        productos = Producto.objects.filter(id__in=self.cart.keys())
        for p in productos:
            qty = self.cart[str(p.id)]["qty"]
            yield {"producto": p, "cantidad": qty, "total": p.precio * qty}

    def total(self):
        total = Decimal("0")
        for p in Producto.objects.filter(id__in=self.cart.keys()):
            total += p.precio * self.cart[str(p.id)]["qty"]
        return total
