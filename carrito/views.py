from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Producto, Orden, OrdenItem
from .cart import Cart, StockInsuficienteError
from .forms import AgregarAlCarritoForm


class ProductoListaView(ListView):
    model = Producto
    paginate_by = 12
    template_name = "carrito/producto_list.html"


class ProductoDetalleView(DetailView):
    model = Producto
    slug_field = "slug"
    template_name = "carrito/producto_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Form conoce el producto para validar stock en clean_cantidad
        ctx["form"] = AgregarAlCarritoForm(producto=self.object)
        return ctx


class CarritoDetalleView(TemplateView):
    template_name = "carrito/carrito_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        ctx["cart"] = cart
        ok, problemas = cart.validar_stock_actual()
        ctx["cart_valido"] = ok
        ctx["cart_problemas"] = problemas
        return ctx


class CarritoAgregarView(View):
    def post(self, request, slug):
        producto = get_object_or_404(Producto, slug=slug)
        form = AgregarAlCarritoForm(request.POST, producto=producto)
        if not form.is_valid():
            # Mensajes de error de form (falta stock, etc.)
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, e)
            return redirect("carrito:producto-detalle", slug=producto.slug)

        try:
            Cart(request).add(producto.id, form.cleaned_data["cantidad"])
            messages.success(request, f"Agregado «{producto.nombre}» al carrito.")
        except StockInsuficienteError as e:
            messages.error(request, str(e))

        return redirect("carrito:carrito-detalle")


class CarritoQuitarView(View):
    def post(self, request, slug):
        producto = get_object_or_404(Producto, slug=slug)
        Cart(request).remove(producto.id)
        messages.info(request, f"Quitaste «{producto.nombre}» del carrito.")
        return redirect("carrito:carrito-detalle")


class SuccessView(TemplateView):
    template_name = "carrito/success.html"


class CheckoutView(LoginRequiredMixin, View):
    login_url = "/admin/login/"

    def get(self, request):
        cart = Cart(request)
        ok, problemas = cart.validar_stock_actual()
        if not ok:
            # Informar al usuario antes de mostrar el checkout
            for p in problemas:
                messages.warning(request, p)
        return render(request, "carrito/checkout.html", {"cart": cart})

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            messages.info(request, "Tu carrito está vacío.")
            return redirect("carrito:carrito-detalle")

        # Validación previa contra stock actual
        ok, problemas = cart.validar_stock_actual()
        if not ok:
            # Ajustar automáticamente al máximo disponible y avisar
            ajustes = cart.asegurar_maximo_disponible()
            for p in problemas:
                messages.error(request, p)
            for a in ajustes:
                messages.warning(request, a)
            return redirect("carrito:carrito-detalle")

        # Crear orden + items y confirmar (descontar stock) de forma atómica
        try:
            with transaction.atomic():
                orden = Orden.objects.create(usuario=request.user)  # estado = borrador por default
                for item in cart:
                    OrdenItem.objects.create(
                        orden=orden,
                        producto=item["producto"],
                        cantidad=item["cantidad"],
                        precio=item["producto"].precio,
                    )
                # Descuenta stock y calcula total/estado
                orden.confirmar()

                # Si todo ok, limpiamos carrito
                cart.clear()

            messages.success(request, f"¡Gracias por tu compra! Orden #{orden.id} confirmada.")
            return redirect("carrito:success")

        except ValidationError as e:
            # Falta de stock detectada al confirmar (concurrencia, etc.)
            messages.error(request, e.message if hasattr(e, "message") else str(e))
            return redirect("carrito:carrito-detalle")
