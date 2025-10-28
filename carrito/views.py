from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Producto, Orden, OrdenItem
from .cart import Cart, StockInsuficienteError
from .forms import AgregarAlCarritoForm, OrdenForm


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


# Antes: SuccessView simple. Ahora: mostramos datos de la orden.
class CheckoutSuccessView(TemplateView):
    template_name = "carrito/success.html"

    def get(self, request, pk):
        orden = get_object_or_404(Orden, pk=pk)
        return render(request, self.template_name, {"orden": orden})


class CheckoutView(View):
    """
    GET: muestra resumen + formulario con datos del comprador.
    POST: valida form, crea orden + items, confirma (descuenta stock) y redirige a success/<pk>/.
    """

    def get(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            messages.info(request, "Tu carrito está vacío.")
            return redirect("carrito:carrito-detalle")

        ok, problemas = cart.validar_stock_actual()
        if not ok:
            for p in problemas:
                messages.warning(request, p)

        # Prefill si está logueado y tenés datos (opcional)
        initial = {}
        form = OrdenForm(initial=initial)
        return render(request, "carrito/checkout.html", {"cart": cart, "form": form})

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            messages.info(request, "Tu carrito está vacío.")
            return redirect("carrito:carrito-detalle")

        ok, problemas = cart.validar_stock_actual()
        if not ok:
            # Ajuste automático para no romper
            ajustes = cart.asegurar_maximo_disponible()
            for p in problemas:
                messages.error(request, p)
            for a in ajustes:
                messages.warning(request, a)
            return redirect("carrito:carrito-detalle")

        form = OrdenForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Revisá los datos del formulario.")
            return render(request, "carrito/checkout.html", {"cart": cart, "form": form})

        try:
            with transaction.atomic():
                # Creamos la orden con los datos del comprador
                orden: Orden = form.save(commit=False)
                if request.user.is_authenticated:
                    orden.usuario = request.user  # opcional
                orden.save()

                # Crear items
                for item in cart:
                    OrdenItem.objects.create(
                        orden=orden,
                        producto=item["producto"],
                        cantidad=item["cantidad"],
                        precio=item["producto"].precio,
                    )

                # Confirmar (descuenta stock, calcula total y marca estado)
                orden.confirmar()

                # Limpiar carrito
                cart.clear()

            messages.success(request, f"¡Gracias por tu compra! Orden #{orden.id} confirmada.")
            return redirect("carrito:success", pk=orden.pk)

        except ValidationError as e:
            messages.error(request, e.message if hasattr(e, "message") else str(e))
            return redirect("carrito:carrito-detalle")
