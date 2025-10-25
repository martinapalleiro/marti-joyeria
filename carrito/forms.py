from django import forms
class AgregarAlCarritoForm(forms.Form):
    cantidad = forms.IntegerField(min_value=1, max_value=20, initial=1)
