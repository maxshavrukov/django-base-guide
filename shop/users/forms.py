from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# 1. Русифицируем стандартную форму входа
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Имя пользователя или Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

# 2. Русифицируем форму регистрации
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")
    
    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Имя пользователя"
        self.fields['email'].label = "Электронная почта"
        # Русифицируем поля паролей
        if 'password1' in self.fields:
            self.fields['password1'].label = "Пароль"
        if 'password2' in self.fields:
            self.fields['password2'].label = "Подтверждение пароля"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким Email уже зарегистрирован.")
        return email
    