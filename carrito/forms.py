from django import forms
from .models import Producto

class AgregarAlCarritoForm(forms.Form):
    cantidad = forms.IntegerField(min_value=1, max_value=100, initial=1)

    def __init__(self, *args, **kwargs):
        # Recibimos el producto al instanciar el form
        self.producto = kwargs.pop("producto", None)
        super().__init__(*args, **kwargs)

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get("cantidad")

        # Si tenemos un producto, validamos el stock disponible
        if self.producto:
            if cantidad > self.producto.stock:
                raise forms.ValidationError(
                    f"Solo hay {self.producto.stock} unidades disponibles de «{self.producto.nombre}»."
                )

        return cantidad
