import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Violation
from .models import plate_regex


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'full_name', 'phone', 'birth_date', 'address',
            'car_brand', 'car_model', 'car_categories', 'vin_number', 'car_year',
            'country', 'license_plate', 'service_id'
        ]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (___) ___-__-__'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'car_brand': forms.TextInput(attrs={'class': 'form-control'}),
            'car_model': forms.TextInput(attrs={'class': 'form-control'}),
            'car_categories': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'B, B1, C, M'}),
            'vin_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '17'}),
            'car_year': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2026'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'А000АА'}),
            'car_region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '777', 'maxlength': '3'}),
            'service_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['full_name', 'phone']:
                field.required = False


class MyRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'phone', 'birth_date', 'address', 'role',
                  'car_brand', 'car_model', 'car_categories', 'vin_number', 'car_year',
                  'country', 'license_plate', 'car_region', 'service_id',
                  'password1', 'password2')
    username = forms.CharField(
        label="Логин",
        help_text="Только английские буквы, цифры и нижнее подчеркивание.",
        widget=forms.TextInput(attrs={'placeholder': 'Напр: nikita_77'}),
        error_messages={'required': 'Логин обязателен для заполнения'}
    )


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("Логин обязателен для заполнения")

        # Проверка на существование пользователя
        from .models import User
        if User.objects.filter(username=username).exists():
            raise ValidationError(f"Пользователь с логином '{username}' уже существует. Выберите другой логин.")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Логин может состоять только из английских букв, цифр и нижнего подчеркивания")
        if len(username) < 3:
            raise ValidationError("Логин должен содержать не менее 3 символов")
        return username
    full_name = forms.CharField(
        label="ФИО",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Иванов Иван Иванович'}),
        error_messages={'required': 'ФИО обязательно для заполнения'}
    )
    phone = forms.CharField(
        label="Номер телефона",
        initial="+7",
        widget=forms.TextInput(attrs={'placeholder': '+7 (___) ___-__-__'}),
        error_messages={'required': 'Номер телефона обязателен для заполнения'}
    )
    birth_date = forms.DateField(
        label="Дата рождения",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'required': 'Дата рождения обязательна для заполнения'}
    )
    address = forms.CharField(
        label="Место жительства",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'г. Москва, ул. Примерная, д. 1, кв. 1'}),
        error_messages={'required': 'Адрес места жительства обязателен для заполнения'}
    )
    role = forms.ChoiceField(
        label="Роль",
        choices=[
            ('driver', 'Водитель'),
            ('inspector', 'Инспектор ДПС'),
            ('manager', 'Руководитель'),
        ],
        initial='driver',
        error_messages={'required': 'Выберите роль пользователя'}
    )

    car_brand = forms.CharField(
        label="Марка автомобиля",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Напр: Toyota, KIA, Lada'})
    )
    car_model = forms.CharField(
        label="Модель автомобиля",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Напр: Camry, Rio, Vesta'})
    )
    car_categories = forms.CharField(
        label="Категории ТС",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'B, B1, C, M (через запятую)'})
    )
    vin_number = forms.CharField(
        label="VIN-номер",
        required=False,
        max_length=17,
        widget=forms.TextInput(attrs={'placeholder': 'XTA12345678901234', 'maxlength': '17'})
    )
    car_year = forms.IntegerField(
        label="Год выпуска",
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '2020', 'min': '1900', 'max': '2026'})
    )

    country = forms.ChoiceField(
        label="Страна",
        choices=[('RUS', 'Россия'), ('BLR', 'Беларусь'), ('KAZ', 'Казахстан')],
        initial='RUS'
    )
    license_plate = forms.CharField(
        label="Номерной знак",
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'А000АА', 'style': 'text-transform: uppercase'})
    )

    service_id = forms.CharField(
        label="Номер служебного удостоверения",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Напр: 123456'})
    )

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Введите пароль'}),
        error_messages={'required': 'Пароль обязателен для заполнения'}
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'}),
        error_messages={'required': 'Подтверждение пароля обязательно'}
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'phone', 'birth_date', 'address', 'role',
                  'car_brand', 'car_model', 'car_categories', 'vin_number', 'car_year',
                  'country', 'license_plate', 'car_region', 'service_id', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'


    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise ValidationError("Пожалуйста, укажите ваше ФИО")
        if len(full_name.strip()) < 5:
            raise ValidationError("ФИО должно содержать хотя бы 5 символов")
        return full_name.strip()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("Логин обязателен для заполнения")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Логин может состоять только из английских букв, цифр и нижнего подчеркивания")
        if len(username) < 3:
            raise ValidationError("Логин должен содержать не менее 3 символов")
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError("Номер телефона обязателен для заполнения")
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10:
            raise ValidationError("Введите корректный номер телефона. Пример: +7 (912) 345-67-89")
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        from datetime import date
        if not birth_date:
            raise ValidationError("Дата рождения обязательна для заполнения")
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise ValidationError(f"Вам {age} лет. Регистрация доступна только с 18 лет")
        return birth_date

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise ValidationError("Пожалуйста, укажите ваш адрес места жительства")
        return address.strip()

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise ValidationError("Пожалуйста, выберите страну регистрации")
        return country

    def clean_car_brand(self):
        car_brand = self.cleaned_data.get('car_brand')
        role = self.cleaned_data.get('role')
        if role == 'driver' and not car_brand:
            raise ValidationError("Для водителя марка автомобиля обязательна")
        return car_brand

    def clean_car_model(self):
        car_model = self.cleaned_data.get('car_model')
        role = self.cleaned_data.get('role')
        if role == 'driver' and not car_model:
            raise ValidationError("Для водителя модель автомобиля обязательна")
        return car_model

    def clean_car_categories(self):
        car_categories = self.cleaned_data.get('car_categories')
        role = self.cleaned_data.get('role')
        if role == 'driver' and not car_categories:
            raise ValidationError("Для водителя категории ТС обязательны")
        return car_categories

    def clean_vin_number(self):
        vin = self.cleaned_data.get('vin_number', '').upper()
        role = self.cleaned_data.get('role')
        if role == 'driver' and not vin:
            raise ValidationError("Для водителя VIN-номер обязателен")
        if vin and len(vin) != 17:
            raise ValidationError(f"VIN-номер должен содержать 17 символов (сейчас {len(vin)})")
        return vin

    def clean_car_year(self):
        year = self.cleaned_data.get('car_year')
        role = self.cleaned_data.get('role')
        from datetime import date
        if role == 'driver' and not year:
            raise ValidationError("Для водителя год выпуска обязателен")
        if year and year > date.today().year:
            raise ValidationError(f"Год выпуска не может быть позже {date.today().year}")
        return year

    def clean_license_plate(self):
        plate = self.cleaned_data.get('license_plate', '').upper()
        role = self.cleaned_data.get('role')
        if role == 'driver' and not plate:
            raise ValidationError("Для водителя номерной знак обязателен")
        if plate and not re.match(r'^[АВЕКМНОРСТУХABEKMHOPCTYX][0-9]{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}$', plate):
            raise ValidationError("Неверный формат госномера. Пример: А123ВС")
        return plate

    def clean_car_region(self):
        region = self.cleaned_data.get('car_region', '')
        role = self.cleaned_data.get('role')
        if role == 'driver' and not region:
            raise ValidationError("Для водителя код региона обязателен")
        if region and not re.match(r'^[0-9]{1,3}$', region):
            raise ValidationError("Код региона может содержать только цифры")
        return region

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not password:
            raise ValidationError("Пароль обязателен для заполнения")
        if len(password) < 10:
            raise ValidationError("Пароль должен содержать не менее 10 символов")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру")
        if not any(c.isalpha() for c in password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву")
        if not any(c in '!@#$%^&*()_+-=[]{};:\'",.<>/?`~' for c in password):
            raise ValidationError("Пароль должен содержать хотя бы один спецсимвол")
        return password

    def clean_service_id(self):
        role = self.cleaned_data.get('role')
        service_id = self.cleaned_data.get('service_id')
        if role in ['inspector', 'manager'] and not service_id:
            raise ValidationError("Сотрудники ГИБДД обязаны указать номер служебного удостоверения")
        if service_id and not re.match(r'^[0-9]{6,10}$', service_id):
            raise ValidationError("Номер удостоверения должен содержать 6-10 цифр")
        return service_id

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Пароли не совпадают")
        return cleaned_data


class ViolationForm(forms.ModelForm):
    driver_fio = forms.CharField(
        max_length=255,
        label="ФИО Водителя",
        help_text="Заполняется вручную инспектором",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Иванов Иван Иванович'})
    )

    car_plate = forms.CharField(
        max_length=15,
        label="Госномер ТС",
        widget=forms.TextInput(
            attrs={'placeholder': 'А000АА777', 'style': 'text-transform: uppercase; font-size: 24px;'})
    )

    article = forms.CharField(
        max_length=50,
        label="Статья КоАП",
        widget=forms.HiddenInput(),
        required=False
    )

    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Сумма штрафа",
        widget=forms.HiddenInput(),
        required=False
    )

    article_manual = forms.CharField(
        max_length=50,
        label="Статья КоАП (вручную)",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ст...'})
    )

    amount_manual = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Сумма штрафа (вручную)",
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '0'})
    )

    class Meta:
        model = Violation
        fields = [
            'driver_fio', 'car_plate', 'car_brand_model',
            'article', 'amount', 'article_manual', 'amount_manual',
            'place', 'violation_datetime', 'vin', 'evidence_img', 'inspector_comment'
        ]
        widgets = {
            'car_brand_model': forms.TextInput(attrs={'placeholder': 'Toyota Camry'}),
            'place': forms.TextInput(attrs={'placeholder': 'г. Москва, ул. Ленина, д.1'}),
            'evidence_img': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'violation_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.inspector = kwargs.pop('inspector', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field.widget.__class__ != forms.HiddenInput:
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'

    def clean_car_plate(self):
        """Проверка госномера """
        plate = self.cleaned_data.get('car_plate', '').upper().strip()
        plate = plate.replace(' ', '').replace('-', '')

        if not plate:
            raise ValidationError("Введите госномер")

        pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$'

        if not re.match(pattern, plate):
            raise ValidationError(
                'Неверный формат госномера. Примеры: А123ВС777, В543ОР99, М777АА178'
            )

        return plate

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Сумма штрафа должна быть больше 0')
        if amount is not None and amount > 500000:
            raise ValidationError('Сумма штрафа не может превышать 500 000 рублей')
        return amount

    def clean_place(self):
        place = self.cleaned_data.get('place', '').strip()
        if not place:
            raise ValidationError('Место нарушения обязательно')
        return place

    def clean(self):
        cleaned_data = super().clean()

        # Получаем значения
        article = cleaned_data.get('article')
        amount = cleaned_data.get('amount')
        article_manual = cleaned_data.get('article_manual')
        amount_manual = cleaned_data.get('amount_manual')

        # Проверка статьи и суммы
        if article_manual and amount_manual:
            cleaned_data['article'] = article_manual
            cleaned_data['amount'] = amount_manual
        elif article and amount:
            pass
        elif article_manual and not amount_manual:
            self.add_error('amount_manual', 'Введите сумму штрафа')
        elif not article_manual and amount_manual:
            self.add_error('article_manual', 'Введите статью КоАП')
        elif not article and not article_manual:
            self.add_error('article_manual', 'Выберите статью из справочника или введите вручную')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get('article_manual'):
            instance.article = self.cleaned_data['article_manual']
        if self.cleaned_data.get('amount_manual'):
            instance.amount = self.cleaned_data['amount_manual']

        if self.inspector:
            instance.inspector = self.inspector

        if commit:
            instance.save()
        return instance