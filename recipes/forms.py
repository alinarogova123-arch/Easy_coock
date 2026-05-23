from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Allergen, FoodType, MenuType, Subscription, SubscriptionPlan
from .services.pricing import calculate_order_price
from .services.promo import find_promo_code, validate_promo_code


PLAN_DURATION_CHOICES = (
    (1, '1 мес.'),
    (3, '3 мес.'),
    (6, '6 мес.'),
    (12, '12 мес.'),
)

PERSON_CHOICES = tuple((persons, str(persons)) for persons in range(1, 7))
BOOLEAN_SELECT_CHOICES = (
    ('1', 'Да'),
    ('0', 'Нет'),
)


def coerce_select_bool(value):
    return str(value) == '1'


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


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': 'Неверный email или пароль.',
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user_model = get_user_model()
            user = user_model.objects.filter(email__iexact=email).first()
            username = user.get_username() if user else ''
            self.user = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
        return cleaned_data

    def get_user(self):
        return self.user


class OrderForm(forms.Form):
    menu_type = forms.ChoiceField(
        label='Тип меню',
        choices=MenuType.choices,
    )
    plan_duration = forms.TypedChoiceField(
        label='Срок подписки',
        choices=PLAN_DURATION_CHOICES,
        coerce=int,
    )
    has_breakfast = forms.TypedChoiceField(
        label='Завтраки',
        choices=BOOLEAN_SELECT_CHOICES,
        coerce=coerce_select_bool,
    )
    has_lunch = forms.TypedChoiceField(
        label='Обеды',
        choices=BOOLEAN_SELECT_CHOICES,
        coerce=coerce_select_bool,
    )
    has_dinner = forms.TypedChoiceField(
        label='Ужины',
        choices=BOOLEAN_SELECT_CHOICES,
        coerce=coerce_select_bool,
    )
    has_dessert = forms.TypedChoiceField(
        label='Десерты',
        choices=BOOLEAN_SELECT_CHOICES,
        coerce=coerce_select_bool,
    )
    persons = forms.TypedChoiceField(
        label='Количество персон',
        choices=PERSON_CHOICES,
        coerce=int,
    )
    excluded_allergens = forms.ModelMultipleChoiceField(
        label='Аллергии',
        queryset=Allergen.objects.all(),
        required=False,
    )
    promo_code = forms.CharField(label='Промокод', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = None
        self.promo_code_obj = None

    def clean_plan_duration(self):
        duration = self.cleaned_data['plan_duration']
        self.plan = SubscriptionPlan.objects.filter(
            duration=duration,
            is_active=True,
        ).first()
        if self.plan is None:
            raise forms.ValidationError(
                'Для выбранного срока подписки нет активного тарифа.'
            )
        return duration

    def clean_promo_code(self):
        code = self.cleaned_data['promo_code'].strip()
        if not code:
            return ''

        promo_code = find_promo_code(code)
        self.promo_code_obj = validate_promo_code(promo_code)
        return code

    def clean(self):
        cleaned_data = super().clean()
        if not self.get_selected_food_types(cleaned_data):
            raise forms.ValidationError(
                'Выберите хотя бы один приём пищи для подписки.'
            )
        return cleaned_data

    def get_selected_food_types(self, cleaned_data=None):
        data = cleaned_data or self.cleaned_data
        selected_food_types = []

        if data.get('has_breakfast'):
            selected_food_types.append(FoodType.BREAKFAST)
        if data.get('has_lunch'):
            selected_food_types.append(FoodType.LUNCH)
        if data.get('has_dinner'):
            selected_food_types.append(FoodType.DINNER)
        if data.get('has_dessert'):
            selected_food_types.append(FoodType.DESSERT)

        return selected_food_types

    def save(self, user):
        selected_food_types = self.get_selected_food_types()
        order_price = calculate_order_price(
            selected_food_types,
            self.plan,
            self.promo_code_obj,
        )

        subscription = Subscription.objects.create(
            user=user,
            plan=self.plan,
            menu_type=self.cleaned_data['menu_type'],
            persons=self.cleaned_data['persons'],
            has_breakfast=self.cleaned_data['has_breakfast'],
            has_lunch=self.cleaned_data['has_lunch'],
            has_dinner=self.cleaned_data['has_dinner'],
            has_dessert=self.cleaned_data['has_dessert'],
            promo_code=self.promo_code_obj,
            total_before_discount=order_price['total_before_discount'],
            discount_amount=order_price['discount_amount'],
            total_paid=order_price['total_paid'],
        )
        subscription.excluded_allergens.set(
            self.cleaned_data['excluded_allergens']
        )
        return subscription
