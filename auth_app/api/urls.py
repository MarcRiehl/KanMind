from django.urls import path
from .views import RegistrationView, LoginView, LogoutView
# from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout') #nur zum testen, danach wieder raus!!!
]