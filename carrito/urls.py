from django.urls import path
from .views import (
    ProductoListaView, ProductoDetalleView,
    CarritoDetalleView, CarritoAgregarView, CarritoQuitarView,
    CheckoutView, CheckoutSuccessView,
)

app_name = "carrito"

urlpatterns = [
    path("",                      ProductoListaView.as_view(),   name="home"),
    path("p/<slug:slug>/",       ProductoDetalleView.as_view(), name="producto-detalle"),
    path("carrito/",             CarritoDetalleView.as_view(),  name="carrito-detalle"),
    path("carrito/add/<slug:slug>/",    CarritoAgregarView.as_view(), name="carrito-agregar"),
    path("carrito/remove/<slug:slug>/", CarritoQuitarView.as_view(),  name="carrito-quitar"),
    path("checkout/",            CheckoutView.as_view(),        name="checkout"),
    path("success/<int:pk>/",    CheckoutSuccessView.as_view(), name="success"),  # <— cambio
]
