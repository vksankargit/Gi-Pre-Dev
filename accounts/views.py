from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordChangeForm
from .models import User
from organizations.models import Organization, OrganizationCoordinator
from .forms import CustomLoginForm, ChangePasswordForm, LoginAsForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        
        if user.is_first_login:
            messages.info(self.request, 'Please change your password before continuing.')
            return redirect('accounts:change_password')
        
        return response


class CustomLogoutView(LogoutView):
    next_page = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        # Clear impersonation session if it exists
        if 'impersonated_user_id' in request.session:
            del request.session['impersonated_user_id']
        if 'original_user_id' in request.session:
            del request.session['original_user_id']

        return super().dispatch(request, *args, **kwargs)


class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = 'accounts/change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        user = self.request.user
        user.is_first_login = False
        user.save()
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)


class ForgotPasswordView(TemplateView):
    template_name = 'accounts/forgot_password.html'


class LoginAsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/login_as.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role == 'coordinator':
            # Get organizations assigned to this coordinator
            organizations = Organization.objects.filter(
                coordinators__coordinator=user,
                coordinators__is_active=True
            )
            context['organizations'] = organizations
        
        return context
    
    def post(self, request, *args, **kwargs):
        organization_id = request.POST.get('organization')
        user_id = request.POST.get('user')
        
        if organization_id and user_id:
            try:
                organization = Organization.objects.get(id=organization_id)
                target_user = User.objects.get(id=user_id, role='general')
                
                # Store impersonation info in session
                request.session['impersonated_user_id'] = target_user.id
                request.session['original_user_id'] = request.user.id
                
                messages.success(request, f'Now logged in as {target_user.get_full_name()}')
                return redirect('dashboard')
                
            except (Organization.DoesNotExist, User.DoesNotExist):
                messages.error(request, 'Invalid selection.')
        
        return render(request, self.template_name, self.get_context_data())


class MyLoginView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        if 'impersonated_user_id' in request.session:
            del request.session['impersonated_user_id']
            del request.session['original_user_id']
            messages.success(request, 'Returned to your original login.')
        
        return redirect('dashboard')