from django import forms
from .models import Producto, Orden, OrdenItem

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "slug", "descripcion", "precio", "stock", "imagen"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

class OrdenForm(forms.ModelForm):
    class Meta:
        model = Orden
        # Solo los campos que tenés en tu modelo:
        fields = ["nombre", "apellido", "dni", "direccion", "metodo_pago"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "dni": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
        }

class OrdenItemForm(forms.ModelForm):
    class Meta:
        model = OrdenItem
        # Según tu checkout, el modelo tiene precio (no precio_unitario)
        fields = ["producto", "cantidad", "precio"]
        widgets = {
            "producto": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
