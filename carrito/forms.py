from django import forms
from .models import Producto, Orden

class AgregarAlCarritoForm(forms.Form):
    cantidad = forms.IntegerField(min_value=1, initial=1)

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


class OrdenForm(forms.ModelForm):
    class Meta:
        model = Orden
        fields = ["nombre", "apellido", "dni", "direccion", "metodo_pago"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "dni": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
        }
