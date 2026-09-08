from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from users.models import UserProfile


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя или Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Электронная почта')

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Электронная почта'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким Email уже зарегистрирован.')
        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'first_name',
            'last_name',
            'phone',
            'birth_date',
            'city',
            'address',
            'postal_code',
        )
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон',
            'birth_date': 'Дата рождения',
            'city': 'Город',
            'address': 'Адрес',
            'postal_code': 'Почтовый индекс',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_birth_date(self):
        value = self.cleaned_data.get('birth_date')
        if self.instance.pk and self.instance.birth_date and value != self.instance.birth_date:
            raise forms.ValidationError(
                'Изменение даты рождения после первого сохранения доступно через администратора.'
            )
        return value
