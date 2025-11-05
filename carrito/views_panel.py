# carrito/views_panel.py

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .models import Producto, Orden, OrdenItem
from .forms_panel import ProductoForm, OrdenForm, OrdenItemForm


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Permite acceso solo a superusuarios."""
    login_url = "/accounts/login/"

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "No tenés permisos para acceder al panel.")
            return redirect("carrito:home")
        return super().handle_no_permission()


class PanelTitleMixin:
    """
    Inyecta nombres legibles del modelo al contexto para usarlos en templates
    (evita acceder a _meta desde las plantillas).
    """
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = getattr(self, "model", None)
        if model:
            verbose = getattr(getattr(model, "_meta", None), "verbose_name", model.__name__)
            verbose_plural = getattr(getattr(model, "_meta", None), "verbose_name_plural", f"{model.__name__}s")
            ctx["model_verbose_name"] = str(verbose)
            ctx["model_verbose_name_plural"] = str(verbose_plural)
        # ¿estamos editando?
        ctx["is_edit"] = bool(getattr(self, "object", None) and getattr(self.object, "pk", None))
        return ctx


class ProdList(SuperuserRequiredMixin, PanelTitleMixin, ListView):
    model = Producto
    paginate_by = 12
    template_name = "panel/prod_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(descripcion__icontains=q)
                | Q(slug__icontains=q)
            )
        return qs


class ProdCreate(SuperuserRequiredMixin, PanelTitleMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "panel/form.html"
    success_url = reverse_lazy("panel:prod-list")

    def form_valid(self, form):
        messages.success(self.request, "Producto creado correctamente.")
        return super().form_valid(form)


class ProdUpdate(SuperuserRequiredMixin, PanelTitleMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "panel/form.html"
    success_url = reverse_lazy("panel:prod-list")

    def form_valid(self, form):
        messages.success(self.request, "Producto actualizado correctamente.")
        return super().form_valid(form)


class ProdDelete(SuperuserRequiredMixin, PanelTitleMixin, DeleteView):
    model = Producto
    template_name = "panel/confirm_delete.html"
    success_url = reverse_lazy("panel:prod-list")

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, "Producto eliminado.")
        return super().delete(request, *args, **kwargs)


class OrdenList(SuperuserRequiredMixin, PanelTitleMixin, ListView):
    model = Orden
    paginate_by = 12
    template_name = "panel/orden_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(apellido__icontains=q)
                | Q(dni__icontains=q)
                | Q(id__icontains=q)
            )
        return qs.order_by("-id")


class OrdenDetail(SuperuserRequiredMixin, PanelTitleMixin, DetailView):
    model = Orden
    template_name = "panel/orden_detail.html"


class OrdenCreate(SuperuserRequiredMixin, PanelTitleMixin, CreateView):
    model = Orden
    form_class = OrdenForm
    template_name = "panel/form.html"

    def get_success_url(self):
        messages.success(self.request, "Orden creada.")
        return reverse("panel:orden-detail", args=[self.object.pk])


class OrdenUpdate(SuperuserRequiredMixin, PanelTitleMixin, UpdateView):
    model = Orden
    form_class = OrdenForm
    template_name = "panel/form.html"

    def get_success_url(self):
        messages.success(self.request, "Orden actualizada.")
        return reverse("panel:orden-detail", args=[self.object.pk])


class OrdenDelete(SuperuserRequiredMixin, PanelTitleMixin, DeleteView):
    model = Orden
    template_name = "panel/confirm_delete.html"
    success_url = reverse_lazy("panel:orden-list")

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, "Orden eliminada.")
        return super().delete(request, *args, **kwargs)


class ItemCreate(SuperuserRequiredMixin, PanelTitleMixin, CreateView):
    model = OrdenItem
    form_class = OrdenItemForm
    template_name = "panel/form.html"

    def form_valid(self, form):
        orden = get_object_or_404(Orden, pk=self.kwargs["orden_id"])
        form.instance.orden = orden
        messages.success(self.request, "Ítem agregado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("panel:orden-detail", args=[self.object.orden_id])


class ItemUpdate(SuperuserRequiredMixin, PanelTitleMixin, UpdateView):
    model = OrdenItem
    form_class = OrdenItemForm
    template_name = "panel/form.html"

    def get_success_url(self):
        messages.success(self.request, "Ítem actualizado.")
        return reverse("panel:orden-detail", args=[self.object.orden_id])


class ItemDelete(SuperuserRequiredMixin, PanelTitleMixin, DeleteView):
    model = OrdenItem
    template_name = "panel/confirm_delete.html"

    def get_success_url(self):
        messages.warning(self.request, "Ítem eliminado.")
        return reverse("panel:orden-detail", args=[self.object.orden_id])

class ProdPreview(SuperuserRequiredMixin, PanelTitleMixin, DetailView):
    model = Producto
    template_name = "panel/prod_preview.html"