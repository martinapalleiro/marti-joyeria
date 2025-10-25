from django.db import models
from django.conf import settings
from django.urls import reverse

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

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("carrito:producto-detalle", args=[self.slug])

class Orden(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Orden #{self.id} - {self.usuario}"

class OrdenItem(models.Model):
    orden = models.ForeignKey(Orden, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio
