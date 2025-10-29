from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Producto


# --- Excepciones específicas del carrito ---
class CartError(Exception):
    """Error genérico del carrito."""


class StockInsuficienteError(CartError):
    """Se intentó poner una cantidad mayor al stock disponible."""


class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[self.SESSION_KEY] = cart
        # dict: { "product_id": {"qty": int} }
        self.cart = cart

    # --- Helpers internos ---
    def _norm_key(self, product_id):
        # Fuerza siempre str de un int (lanza ValueError si no es convertible)
        return str(int(product_id))

    def _mark_modified(self):
        self.session.modified = True

    def _get_producto(self, product_id) -> Producto:
        pid = int(product_id)
        return Producto.objects.get(id=pid)

    def _get_current_qty(self, product_id) -> int:
        return int(self.cart.get(self._norm_key(product_id), {}).get("qty", 0))

    # --- API pública ---

    def add(self, product_id, qty=1, override=False):
        """
        Agrega o establece cantidad para un producto.
        - Si override=False (default), suma 'qty' a lo que ya había.
        - Si override=True, reemplaza por 'qty' exacto.

        Valida stock:
        - Si la cantidad final requerida supera el stock, levanta StockInsuficienteError.

        No devuelve nada; si no hay error, deja el carrito actualizado.
        """
        key = self._norm_key(product_id)
        qty = int(qty)

        if qty < 0:
            raise ValidationError("La cantidad no puede ser negativa.")

        producto = self._get_producto(product_id)
        actual = 0 if override else self._get_current_qty(product_id)
        nueva_cantidad = qty if override else (actual + qty)

        if nueva_cantidad <= 0:
            # Quitar si quedó en 0 o menos
            self.cart.pop(key, None)
            self._mark_modified()
            return

        if nueva_cantidad > producto.stock:
            raise StockInsuficienteError(
                f"Solo hay {producto.stock} unidades disponibles de «{producto.nombre}»."
            )

        # OK: guardar
        self.cart[key] = {"qty": nueva_cantidad}
        self._mark_modified()

    def set(self, product_id, qty):
        """
        Establece (override) la cantidad exacta de un producto.
        Alias cómodo de add(..., override=True).
        """
        return self.add(product_id, qty=qty, override=True)

    def increment(self, product_id, step=1):
        """
        Incrementa en 'step' (positivo o negativo) respetando stock.
        """
        return self.add(product_id, qty=step, override=False)

    def remove(self, product_id):
        key = self._norm_key(product_id)
        if key in self.cart:
            del self.cart[key]
            self._mark_modified()

    def clear(self):
        self.session[self.SESSION_KEY] = {}
        self.cart = self.session[self.SESSION_KEY]
        self._mark_modified()

    def __len__(self):
        # cantidad total de unidades
        total_qty = 0
        for v in self.cart.values():
            try:
                total_qty += int(v.get("qty", 0))
            except (TypeError, ValueError):
                continue
        return total_qty

    @property
    def total(self):
        # total en dinero
        total = Decimal("0.00")
        for item in self:
            total += item["subtotal"]
        return total

    def _numeric_keys(self):
        """Devuelve solo las claves numéricas; elimina basura del carrito."""
        numeric_keys = []
        dirty = False
        for k in list(self.cart.keys()):
            try:
                numeric_keys.append(int(k))
            except (TypeError, ValueError):
                # limpiar entrada inválida
                self.cart.pop(k, None)
                dirty = True
        if dirty:
            self._mark_modified()
        return numeric_keys

    def __iter__(self):
        """
        Rinde items con estructura:
        {
            "producto": Producto,
            "cantidad": int,
            "subtotal": Decimal,
            "stock_disponible": int,   # útil para UI
            "valido": bool             # True si cantidad <= stock actual
        }
        """
        ids = self._numeric_keys()  # <- filtra y limpia
        if not ids:
            return
        productos = {p.id: p for p in Producto.objects.filter(id__in=ids)}
        for pid in ids:
            pdata = self.cart.get(str(pid), {})
            try:
                qty = int(pdata.get("qty", 0))
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                continue
            producto = productos.get(pid)
            if not producto:
                # si el producto ya no existe, limpia la entrada
                self.cart.pop(str(pid), None)
                self._mark_modified()
                continue

            valido = qty <= producto.stock
            yield {
                "producto": producto,
                "cantidad": qty,
                "subtotal": producto.precio * qty,
                "stock_disponible": producto.stock,
                "valido": valido,
            }


    def validar_stock_actual(self):
        """
        Revisa el carrito contra el stock actual de BD.
        Devuelve (ok, problemas) donde:
          - ok es True si TODO está dentro de stock,
          - problemas es una lista de strings explicando faltantes.
        No modifica el carrito.
        """
        problemas = []
        for item in self:
            if not item["valido"]:
                p = item["producto"]
                problemas.append(
                    f"«{p.nombre}»: pedido {item['cantidad']}, disponible {item['stock_disponible']}"
                )
        return (len(problemas) == 0, problemas)

    def asegurar_maximo_disponible(self):
        """
        Ajusta (reduce) las cantidades que exceden el stock actual.
        Devuelve lista de mensajes con los cambios realizados.
        """
        mensajes = []
        ids = self._numeric_keys()
        if not ids:
            return mensajes

        productos = {p.id: p for p in Producto.objects.filter(id__in=ids)}
        changed = False

        for pid in ids:
            key = str(pid)
            pdata = self.cart.get(key, {})
            try:
                qty = int(pdata.get("qty", 0))
            except (TypeError, ValueError):
                qty = 0

            p = productos.get(pid)
            if not p:
                # limpia si el producto ya no existe
                self.cart.pop(key, None)
                changed = True
                continue

            if qty > p.stock:
                # si no hay nada, eliminar; si hay, capear
                if p.stock <= 0:
                    self.cart.pop(key, None)
                    mensajes.append(f"«{p.nombre}» se quitó: sin stock disponible.")
                else:
                    self.cart[key] = {"qty": p.stock}
                    mensajes.append(
                        f"«{p.nombre}» ajustado a {p.stock} por stock limitado."
                    )
                changed = True

        if changed:
            self._mark_modified()

        return mensajes
