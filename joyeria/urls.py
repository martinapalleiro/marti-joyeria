"""
URL configuration for joyeria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# joyeria/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ⬇️ Importamos el LoginView y tu form de login con Bootstrap
from django.contrib.auth.views import LoginView
from carrito.forms_auth import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),

    # Sitio / tienda
    path("", include(("carrito.urls", "carrito"), namespace="carrito")),

    # Panel (tus CBVs del panel ya tienen el mixin de superusuario)
    path("panel/", include("carrito.urls_panel", namespace="panel")),

    # ⬇️ Login personalizado (tiene que ir ANTES del include genérico)
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=LoginForm,
        ),
        name="login",
    ),

    # Resto de URLs de auth (logout, reset, etc.)
    path("accounts/", include("django.contrib.auth.urls")),
]

# Media en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
