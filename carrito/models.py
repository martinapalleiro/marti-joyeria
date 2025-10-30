# models.py
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Q, Sum, DecimalField
from django.urls import reverse
from django.core.exceptions import ValidationError

class Producto(models.Model):
    nombre = models.CharField(max_length=120)              # obligatorio
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)             # opcional
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(check=Q(stock__gte=0), name="producto_stock_no_negativo"),
        ]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("carrito:producto-detalle", args=[self.slug])

    def tiene_stock(self, cantidad: int) -> bool:
        return self.stock >= int(cantidad)

    def descontar_stock(self, cantidad: int) -> bool:
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
    # TODOS OBLIGATORIOS (sin default, sin blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20)
    direccion = models.TextField()

    # Para obligar selección, no ponemos default ni blank=True
    metodo_pago = models.CharField(
        max_length=30,
        choices=[
            ("tarjeta", "Tarjeta de crédito/débito"),
            ("mercadopago", "MercadoPago"),
            ("efectivo", "Efectivo/Pago en sucursal"),
        ],
    )

    # Si querés que requiera login, sacá null/blank:
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        # Para checkout SÍ o SÍ logueado, usá:
        # null=False, blank=False
        null=True, blank=True,
    )

    creado = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estado = models.CharField(max_length=12, choices=ESTADOS, default="borrador")

    def __str__(self):
        quien = f"{self.nombre} {self.apellido}".strip() or str(self.usuario) or "Invitado"
        return f"Orden #{self.id} - {quien} ({self.estado})"

    @property
    def comprador(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    def calcular_total(self) -> Decimal:
        agg = self.items.aggregate(
            s=Sum(F("cantidad") * F("precio"), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
        return agg["s"] or Decimal("0.00")

    @transaction.atomic
    def confirmar(self):
        producto_ids = list(self.items.values_list("producto_id", flat=True))
        productos_bloqueados = Producto.objects.select_for_update().filter(id__in=producto_ids)
        productos_map = {p.id: p for p in productos_bloqueados}

        faltantes = []
        for item in self.items.select_related("producto"):
            prod = productos_map[item.producto_id]
            if not prod.descontar_stock(item.cantidad):
                prod.refresh_from_db(fields=["stock"])
                faltantes.append(f"«{prod.nombre}»: pedido {item.cantidad}, disponible {prod.stock}")

        if faltantes:
            raise ValidationError("No hay stock suficiente para: " + "; ".join(faltantes))

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
        if self._state.adding and (self.precio is None or self.precio == 0):
            self.precio = self.producto.precio
        super().save(*args, **kwargs)
