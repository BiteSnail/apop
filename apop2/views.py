from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class MyLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"
    redirect_field_name = "redirect_to"


class HomeView(TemplateView, MyLoginRequiredMixin):
    template_name='main.html'
