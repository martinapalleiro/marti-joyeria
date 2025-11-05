from django.urls import path
from . import views_panel as v

app_name = "panel"

urlpatterns = [
    # Productos
    path("productos/", v.ProdList.as_view(), name="prod-list"),
    path("productos/crear/", v.ProdCreate.as_view(), name="prod-create"),
    path("productos/<int:pk>/editar/", v.ProdUpdate.as_view(), name="prod-update"),
    path("productos/<int:pk>/eliminar/", v.ProdDelete.as_view(), name="prod-delete"),
    path("productos/<int:pk>/ver/", v.ProdPreview.as_view(), name="prod-preview"),

]
