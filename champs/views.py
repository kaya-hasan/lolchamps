from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import logout
from .models import Champion, Role, Review
from .forms import ReviewForm, ChampionForm
from django.utils.text import slugify
from django.db.models import Q
from django.core.paginator import Paginator

# Create your views here.
def home(request):
    stats = {
        "champion_count": Champion.objects.count(),
        "role_count": Role.objects.count(),
        "review_count": Review.objects.count(),
    }
    return render(request, "champs/home.html", stats)

# Şampiyon listesi
def champion_list(request):
    champs = Champion.objects.select_related("role")
    role_id = request.GET.get("role_id")
    selected_role = None
    q = request.GET.get("q", "").strip()
    selected_sort = request.GET.get("sort", "newest")

    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "name_asc": "name",
        "name_desc": "-name",
        "tier_asc": "tier",
        "tier_desc": "-tier",
        "difficulty_asc": "difficulty",
        "difficulty_desc": "-difficulty",
    }

    if role_id:
        try:
            selected_role = int(role_id)
            champs = champs.filter(role_id=selected_role)
        except (TypeError, ValueError):
            selected_role = None
    if q:
        champs = champs.filter(Q(name__icontains=q) | Q(lore__icontains=q))

    champs = champs.order_by(sort_map.get(selected_sort, "-created_at"))
    paginator = Paginator(champs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    roles = Role.objects.all()
    context = {
        'champs': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.paginator.num_pages > 1,
        'roles': roles,
        'selected_role': selected_role,
        'q': q,
        'selected_sort': selected_sort,
    }
    return render(request, 'champs/champion_list.html', context)

def champion_detail(request, slug):
    champion = get_object_or_404(Champion, slug=slug)
    reviews = champion.reviews.select_related("user")
    build_insight = getattr(champion, "build_insight", None)
    context = {
        'champion': champion,
        'reviews': reviews,
        'build_insight': build_insight,
    }
    if request.user.is_authenticated:
        context["review_form"] = ReviewForm()
    return render(request, 'champs/champion_detail.html', context)
"""
class ChampionListView(ListView):
    model = Champion
    template_name = 'champs/champion_list.html'
    context_object_name = 'champions'
    ordering = ['name']
    paginate_by = 10

    def get_queryset(self):
        gs = Champion.objects.select.related('role')
        role_id = self.request.GET.get('role_id')
        if role_id:
            gs = gs.filter(role_id=role_id)
        return gs

class ChampionDetailView(DetailView):
    model = Champion
    template_name = 'champs/champion_detail.html'
    context_object_name = 'champion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.select_related("user")
        if self.request.user.is_authenticated:
          already_reviewed = Review.objects.filter(champion=self.object, user=self.request.user).exists()
        if not already_reviewed:
          context["form"] = ReviewForm()
        return context
"""

class RoleDetailView(DetailView):
    model = Role
    template_name = 'champs/role_detail.html'
    context_object_name = 'role'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['champions'] = self.object.champions.all()
        return context

class RoleCreateView(LoginRequiredMixin, CreateView):
    login_url = "/admin/login/"
    model = Role
    fields = ["name", "description"]
    template_name = "champs/role_form.html"
    success_url = reverse_lazy("champs:champion_create")

class ChampionCreateView(LoginRequiredMixin, CreateView):
    login_url = "/admin/login/"
    model = Champion
    form_class = ChampionForm
    template_name = 'champs/champion_form.html'
    success_url = reverse_lazy('champs:champion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_count"] = Role.objects.count()
        return context

    def form_valid(self, form):
        form.instance.slug = slugify(form.instance.name)
        return super().form_valid(form)

class ChampionUpdateView(LoginRequiredMixin, UpdateView):
    login_url = "/admin/login/"
    model = Champion
    form_class = ChampionForm
    template_name = 'champs/champion_form.html'
    success_url = reverse_lazy('champs:champion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_count"] = Role.objects.count()
        return context

    def form_valid(self, form):
        form.instance.slug = slugify(form.instance.name)
        return super().form_valid(form)

class ChampionDeleteView(LoginRequiredMixin, DeleteView):
    login_url = "/admin/login/"
    model = Champion
    template_name = 'champs/champion_confirm_delete.html'
    success_url = reverse_lazy('champs:champion_list')

@login_required
def add_review(request, slug):
    champion = get_object_or_404(Champion, slug=slug)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.champion = champion
            review.user = request.user
            review.save()
            messages.success(request, 'Yorumunuz başarıyla eklendi.')
            return redirect('champs:champion_detail', slug=slug)
        messages.error(request, 'Yorumunuz eklenirken bir hata oluştu.')
    else:
        form = ReviewForm()
    return render(request, 'champs/review_form.html', {'form': form, 'champion': champion})

@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Çıkış yapıldı.")
    return redirect("home")
