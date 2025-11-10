# Abstract Person Model

## Опис

Абстрактна модель `abstract.person` є базовою моделлю для всіх моделей, що представляють осіб (людей) у системі. Вона містить загальні поля та методи, які можуть бути використані у будь-якій моделі, що наслідує від неї.

## Наслідування

```python
class MyPersonModel(models.Model):
    _name = 'my.person.model'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'  # Рекомендовано
```

## Поля

### ПІБ (Обов'язкові поля для формування імені)

- **last_name** (Char, required, indexed)
  - Прізвище особи
  - Обов'язкове для заповнення
  - Індексоване для швидкого пошуку

- **first_name** (Char, required, indexed)
  - Ім'я особи
  - Обов'язкове для заповнення
  - Індексоване для швидкого пошуку

- **middle_name** (Char)
  - По батькові
  - Необов'язкове поле

### Контактна інформація

- **phone** (Char)
  - Номер телефону
  - Валідується за міжнародним форматом
  - Приклади: `+380501234567`, `(123) 456-7890`

- **email** (Char)
  - Електронна пошта
  - Валідується за стандартним форматом email
  - Приклад: `example@domain.com`

### Особиста інформація

- **gender** (Selection)
  - Стать
  - Можливі значення:
    - `male` - Чоловік
    - `female` - Жінка
    - `other` - Інше

- **date_of_birth** (Date)
  - Дата народження
  - Не може бути у майбутньому
  - Вік не може перевищувати 150 років

### Обчислювальні поля (computed, stored)

- **age** (Integer, readonly)
  - Вік особи
  - Автоматично обчислюється від дати народження
  - Враховує місяць та день народження
  - Зберігається у базі даних (stored=True)
  - Оновлюється при зміні `date_of_birth`

- **full_name** (Char, readonly, indexed)
  - Повне ім'я
  - Формується як: "Прізвище Ім'я По батькові"
  - Зберігається у базі даних (stored=True)
  - Індексоване для швидкого пошуку
  - Оновлюється при зміні будь-якого з полів ПІБ

### Додаткова інформація

- **country_id** (Many2one -> res.country)
  - Країна громадянства
  - Посилання на модель країн Odoo

- **lang_id** (Many2one -> res.lang)
  - Мова спілкування
  - Посилання на модель мов Odoo

### Поля зображень (від image.mixin)

- **image_1920** - Оригінальне зображення (1920x1920)
- **image_1024** - Зменшена версія (1024x1024)
- **image_512** - Зменшена версія (512x512)
- **image_256** - Зменшена версія (256x256)
- **image_128** - Зменшена версія (128x128)

## Методи

### _compute_age()

Обчислює вік особи від дати народження.

```python
@api.depends('date_of_birth')
def _compute_age(self):
    """Обчислення віку від дати народження"""
```

**Особливості:**
- Враховує повну дату (рік, місяць, день)
- Якщо дата народження не вказана, вік встановлюється у 0

### _compute_full_name()

Формує повне ім'я з окремих полів ПІБ.

```python
@api.depends('last_name', 'first_name', 'middle_name')
def _compute_full_name(self):
    """Обчислення повного імені"""
```

**Особливості:**
- Об'єднує всі заповнені поля через пробіл
- Пропускає порожні поля

### _check_phone()

Валідує формат телефонного номера.

```python
@api.constrains('phone')
def _check_phone(self):
    """Валідація формату телефону"""
```

**Прийняті формати:**
- Міжнародний: `+380501234567`
- З дужками: `(123) 456-7890`
- З дефісами та пробілами

### _check_email()

Валідує формат електронної пошти.

```python
@api.constrains('email')
def _check_email(self):
    """Валідація формату email"""
```

**Формат:** `username@domain.extension`

### _check_date_of_birth()

Валідує дату народження.

```python
@api.constrains('date_of_birth')
def _check_date_of_birth(self):
    """Валідація дати народження"""
```

**Перевірки:**
- Дата не може бути у майбутньому
- Вік не може перевищувати 150 років

## Приклад використання

### Створення моделі, що наслідує abstract.person

```python
from odoo import fields, models


class Employee(models.Model):
    _name = 'company.employee'
    _description = 'Company Employee'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'

    # Специфічні поля для працівника
    employee_number = fields.Char(
        string='Employee Number',
        required=True,
    )
    department_id = fields.Many2one(
        comodel_name='company.department',
        string='Department',
    )
    position = fields.Char(
        string='Position',
    )
```

### Створення запису

```python
# Через XML
<record id="employee_demo_1" model="company.employee">
    <field name="last_name">Smith</field>
    <field name="first_name">John</field>
    <field name="middle_name">Michael</field>
    <field name="email">john.smith@company.com</field>
    <field name="phone">+380501234567</field>
    <field name="gender">male</field>
    <field name="date_of_birth">1985-05-15</field>
    <field name="employee_number">EMP001</field>
</record>

# Через Python
employee = self.env['company.employee'].create({
    'last_name': 'Smith',
    'first_name': 'John',
    'middle_name': 'Michael',
    'email': 'john.smith@company.com',
    'phone': '+380501234567',
    'gender': 'male',
    'date_of_birth': '1985-05-15',
    'employee_number': 'EMP001',
})

# full_name та age обчислюються автоматично
print(employee.full_name)  # "Smith John Michael"
print(employee.age)  # обчислений вік
```

### Використання у views

```xml
<!-- Tree View -->
<tree>
    <field name="full_name"/>
    <field name="phone"/>
    <field name="email"/>
    <field name="age"/>
</tree>

<!-- Form View -->
<form>
    <sheet>
        <field name="image_1920" widget="image" class="oe_avatar"/>
        <div class="oe_title">
            <h1>
                <field name="full_name" readonly="1"/>
            </h1>
        </div>
        <group>
            <group string="Personal Information">
                <field name="last_name"/>
                <field name="first_name"/>
                <field name="middle_name"/>
                <field name="gender"/>
                <field name="date_of_birth"/>
                <field name="age" readonly="1"/>
            </group>
            <group string="Contact Information">
                <field name="phone"/>
                <field name="email"/>
                <field name="country_id"/>
                <field name="lang_id"/>
            </group>
        </group>
    </sheet>
</form>
```

## Рекомендації

1. **Використовуйте _rec_name**: Завжди встановлюйте `_rec_name = 'full_name'` у моделях, що наслідують abstract.person
2. **Readonly для computed полів**: Поля `full_name` та `age` є computed, тому завжди робіть їх readonly у views
3. **Валідація**: Враховуйте, що валідація телефону та email працює автоматично
4. **Перекриття методів**: Якщо потрібно змінити логіку обчислення, можна перекрити методи у дочірній моделі

## Залежності

Модуль вимагає наступних залежностей:
- `base` - базовий модуль Odoo
- `web` - для image.mixin

## Автор

Khatrus Zakhar
