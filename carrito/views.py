from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Producto, Orden, OrdenItem
from .cart import Cart
from .forms import AgregarAlCarritoForm

class ProductoListaView(ListView):
    model = Producto
    paginate_by = 12
    template_name = "carrito/producto_list.html"

class ProductoDetalleView(DetailView):
    model = Producto
    slug_field = "slug"
    template_name = "carrito/producto_detail.html"

class CarritoDetalleView(TemplateView):
    template_name = "carrito/carrito_detail.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cart"] = Cart(self.request)
        return ctx

class CarritoAgregarView(View):
    def post(self, request, slug):
        producto = get_object_or_404(Producto, slug=slug)
        form = AgregarAlCarritoForm(request.POST)
        if form.is_valid():
            Cart(request).add(producto.id, form.cleaned_data["cantidad"])
        return redirect("carrito:carrito-detalle")

class CarritoQuitarView(View):
    def post(self, request, slug):
        producto = get_object_or_404(Producto, slug=slug)
        Cart(request).remove(producto.id)
        return redirect("carrito:carrito-detalle")

class CheckoutView(LoginRequiredMixin, View):
    login_url = "/admin/login/"
    def get(self, request):
        return render(request, "carrito/checkout.html", {"cart": Cart(request)})
    def post(self, request):
        cart = Cart(request)
        # si está vacío, volver
        if not any(True for _ in cart):
            return redirect("carrito:carrito-detalle")
        orden = Orden.objects.create(usuario=request.user, total=cart.total())
        for item in cart:
            OrdenItem.objects.create(
                orden=orden, producto=item["producto"],
                cantidad=item["cantidad"], precio=item["producto"].precio
            )
        cart.clear()
        return render(request, "carrito/success.html", {"orden": orden})
