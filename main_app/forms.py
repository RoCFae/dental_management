from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


# custom authentication backend that allows users to log in using their email
class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try to fetch the user with the provided email
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        # Check if the password is correct
        if user.check_password(password):
            return user
        return None