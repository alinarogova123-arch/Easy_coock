from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')
        labels = {
            'username': 'Имя',
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Пользователь с таким email уже зарегистрирован.'
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
