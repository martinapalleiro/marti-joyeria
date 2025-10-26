from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Q, Sum, DecimalField
from django.urls import reverse
from django.core.exceptions import ValidationError


class Producto(models.Model):
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(check=Q(stock__gte=0), name="producto_stock_no_negativo"),
        ]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("carrito:producto-detalle", args=[self.slug])

    # Helpers de stock
    def tiene_stock(self, cantidad: int) -> bool:
        return self.stock >= int(cantidad)

    def descontar_stock(self, cantidad: int) -> bool:
        """
        Intenta descontar stock de forma atómica.
        Devuelve True si pudo descontar; False si no había stock suficiente.
        """
        cantidad = int(cantidad)
        if cantidad <= 0:
            return True
        updated = (
            Producto.objects
            .filter(pk=self.pk, stock__gte=cantidad)
            .update(stock=F("stock") - cantidad)
        )
        if updated:
            self.refresh_from_db(fields=["stock"])
            return True
        return False

    def reponer_stock(self, cantidad: int) -> None:
        cantidad = int(cantidad)
        if cantidad <= 0:
            return
        Producto.objects.filter(pk=self.pk).update(stock=F("stock") + cantidad)
        self.refresh_from_db(fields=["stock"])


class Orden(models.Model):
    ESTADOS = (
        ("borrador", "Borrador"),
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estado = models.CharField(max_length=12, choices=ESTADOS, default="borrador")

    def __str__(self):
        return f"Orden #{self.id} - {self.usuario} ({self.estado})"

    def calcular_total(self) -> Decimal:
        agg = self.items.aggregate(
            s=Sum(F("cantidad") * F("precio"), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
        return agg["s"] or Decimal("0.00")

    @transaction.atomic
    def confirmar(self):
        """
        Confirma la orden:
        - Valida stock de cada item.
        - Descuenta stock de forma atómica.
        - Calcula y guarda el total.
        Si falta stock, revierte todo y lanza ValidationError.
        """
        # Bloqueamos filas de productos involucrados para evitar overselling concurrente
        producto_ids = list(self.items.values_list("producto_id", flat=True))
        productos_bloqueados = (
            Producto.objects.select_for_update().filter(id__in=producto_ids)
        )
        productos_map = {p.id: p for p in productos_bloqueados}

        # Validación + descuento
        faltantes = []
        for item in self.items.select_related("producto"):
            prod = productos_map[item.producto_id]
            if not prod.descontar_stock(item.cantidad):
                prod.refresh_from_db(fields=["stock"])
                faltantes.append(
                    f"«{prod.nombre}»: pedido {item.cantidad}, disponible {prod.stock}"
                )

        if faltantes:
            # Cualquier fallo cancela la transacción
            raise ValidationError(
                "No hay stock suficiente para: " + "; ".join(faltantes)
            )

        # Todo ok: set total y estado
        self.total = self.calcular_total()
        self.estado = "confirmada"
        self.save(update_fields=["total", "estado"])


class OrdenItem(models.Model):
    orden = models.ForeignKey(Orden, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self) -> Decimal:
        return Decimal(self.cantidad) * self.precio

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    def save(self, *args, **kwargs):
        """
        Si no se seteó manualmente, toma el precio vigente del producto al crear el item.
        """
        if self._state.adding and (self.precio is None or self.precio == 0):
            self.precio = self.producto.precio
        super().save(*args, **kwargs)
