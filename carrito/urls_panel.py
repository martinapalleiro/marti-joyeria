from django.urls import path
from . import views_panel as v

app_name = "panel"

urlpatterns = [
    # Productos
    path("productos/", v.ProdList.as_view(), name="prod-list"),
    path("productos/crear/", v.ProdCreate.as_view(), name="prod-create"),
    path("productos/<int:pk>/editar/", v.ProdUpdate.as_view(), name="prod-update"),
    path("productos/<int:pk>/eliminar/", v.ProdDelete.as_view(), name="prod-delete"),

    # Órdenes
    path("ordenes/", v.OrdenList.as_view(), name="orden-list"),
    path("ordenes/crear/", v.OrdenCreate.as_view(), name="orden-create"),
    path("ordenes/<int:pk>/", v.OrdenDetail.as_view(), name="orden-detail"),
    path("ordenes/<int:pk>/editar/", v.OrdenUpdate.as_view(), name="orden-update"),
    path("ordenes/<int:pk>/eliminar/", v.OrdenDelete.as_view(), name="orden-delete"),

    # Ítems de orden
    path("ordenes/<int:orden_id>/items/crear/", v.ItemCreate.as_view(), name="item-create"),
    path("items/<int:pk>/editar/", v.ItemUpdate.as_view(), name="item-update"),
    path("items/<int:pk>/eliminar/", v.ItemDelete.as_view(), name="item-delete"),
]
