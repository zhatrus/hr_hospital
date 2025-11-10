# Contact Person Model (hr.hospital.contact.person)

## Опис

Модель `hr.hospital.contact.person` представляє контактних осіб, пов'язаних з пацієнтами. Це можуть бути родичі, друзі, колеги або будь-які інші особи, які можуть бути контактовані у зв'язку з пацієнтом, особливо в екстрених ситуаціях.

## Наслідування

```python
class HrHospitalContactPerson(models.Model):
    _name = 'hr.hospital.contact.person'
    _description = 'Hospital Contact Person'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'
```

Модель успадковує всі поля та методи від `abstract.person`:
- ПІБ (last_name, first_name, middle_name)
- Контактна інформація (phone, email)
- Особиста інформація (gender, date_of_birth)
- Обчислювальні поля (age, full_name)
- Додаткові поля (country_id, lang_id)
- Підтримка аватарів (image fields)

## Специфічні поля

### relationship (Selection)
Тип відносин з пацієнтом.

**Можливі значення:**
- `spouse` - Дружина/Чоловік
- `parent` - Батько/Мати
- `child` - Син/Дочка
- `sibling` - Брат/Сестра
- `friend` - Друг/Подруга
- `colleague` - Колега
- `other` - Інше

**Приклад:**
```python
contact.relationship = 'spouse'
```

### is_emergency_contact (Boolean)
Чи є контактна особа екстреним контактом.

**За замовчуванням:** `False`

**Використання:**
```python
contact.is_emergency_contact = True  # Позначити як екстрений контакт
```

### notes (Text)
Додаткові примітки про контактну особу.

**Приклад:**
```python
contact.notes = "Available 24/7. Speaks English and Ukrainian."
```

### patient_id (Many2one)
Зв'язок з пацієнтом.

**Comodel:** `hr.hospital.patient`  
**Ondelete:** `cascade` (при видаленні пацієнта, контактні особи також видаляються)

**Приклад:**
```python
contact.patient_id = patient_record
```

### active (Boolean)
Активний статус контактної особи.

**За замовчуванням:** `True`

**Використання:**
```python
contact.active = False  # Заархівувати контакт
```

## Використання

### Створення контактної особи

#### Через Python код:
```python
contact = self.env['hr.hospital.contact.person'].create({
    'last_name': 'Smith',
    'first_name': 'John',
    'relationship': 'spouse',
    'phone': '+380501234567',
    'email': 'john.smith@example.com',
    'gender': 'male',
    'date_of_birth': '1980-05-15',
    'is_emergency_contact': True,
    'patient_id': patient.id,
    'notes': 'Primary emergency contact. Available 24/7.',
})
```

#### Через XML:
```xml
<record id="contact_person_demo_1" model="hr.hospital.contact.person">
    <field name="last_name">Smith</field>
    <field name="first_name">John</field>
    <field name="relationship">spouse</field>
    <field name="phone">+380501234567</field>
    <field name="email">john.smith@example.com</field>
    <field name="gender">male</field>
    <field name="date_of_birth">1980-05-15</field>
    <field name="is_emergency_contact" eval="True"/>
    <field name="patient_id" ref="patient_demo_1"/>
    <field name="notes">Primary emergency contact.</field>
</record>
```

### Зв'язок з пацієнтом

У моделі Patient додано поле `contact_person_ids`:

```python
# У моделі Patient
patient.contact_person_ids  # Доступ до всіх контактних осіб пацієнта

# Додавання контактної особи
patient.write({
    'contact_person_ids': [(0, 0, {
        'last_name': 'Doe',
        'first_name': 'Jane',
        'relationship': 'sibling',
        'phone': '+380501234568',
        'is_emergency_contact': True,
    })]
})
```

### Пошук контактних осіб

#### Екстрені контакти:
```python
emergency_contacts = self.env['hr.hospital.contact.person'].search([
    ('is_emergency_contact', '=', True)
])
```

#### Контакти конкретного пацієнта:
```python
patient_contacts = self.env['hr.hospital.contact.person'].search([
    ('patient_id', '=', patient_id)
])
```

#### Контакти за типом відносин:
```python
spouses = self.env['hr.hospital.contact.person'].search([
    ('relationship', '=', 'spouse')
])
```

## Views

### Tree View
Відображає список контактних осіб з основною інформацією:
- Повне ім'я
- Тип відносин
- Телефон
- Email
- Чи є екстреним контактом
- Пов'язаний пацієнт

### Form View
Детальна форма з трьома групами полів:
1. **Personal Information** - особиста інформація
2. **Contact Information** - контактні дані
3. **Relationship Information** - інформація про зв'язок з пацієнтом

Також включає:
- Аватар
- Повне ім'я в заголовку
- Поле для приміток

### Search View
Включає:
- Пошук за полями: full_name, phone, email, patient_id
- Фільтри:
  - Emergency Contacts (екстрені контакти)
  - Active (активні)
  - Archived (заархівовані)
- Групування за:
  - Relationship (тип відносин)
  - Patient (пацієнт)
  - Emergency Contact (екстрений контакт)

## Меню

Контактні особи доступні через:
**Hospital → Contact Persons**

Sequence: 30 (між Doctors та Configuration)

## Права доступу

Всі користувачі з групи `base.group_user` мають повний доступ:
- Read (читання)
- Write (запис)
- Create (створення)
- Unlink (видалення)

## Приклади використання

### Отримання всіх екстрених контактів пацієнта:
```python
def get_emergency_contacts(self, patient_id):
    return self.env['hr.hospital.contact.person'].search([
        ('patient_id', '=', patient_id),
        ('is_emergency_contact', '=', True),
    ])
```

### Перевірка наявності екстреного контакту:
```python
def has_emergency_contact(self, patient_id):
    count = self.env['hr.hospital.contact.person'].search_count([
        ('patient_id', '=', patient_id),
        ('is_emergency_contact', '=', True),
    ])
    return count > 0
```

### Отримання контактних даних для сповіщення:
```python
def get_notification_contacts(self, patient_id):
    contacts = self.env['hr.hospital.contact.person'].search([
        ('patient_id', '=', patient_id),
        ('active', '=', True),
    ])
    return [{
        'name': c.full_name,
        'phone': c.phone,
        'email': c.email,
        'is_emergency': c.is_emergency_contact,
    } for c in contacts]
```

## Валідація

Модель успадковує всю валідацію від `abstract.person`:
- ✅ Валідація телефону (міжнародний формат)
- ✅ Валідація email (стандартний формат)
- ✅ Валідація дати народження (не у майбутньому, вік до 150 років)

## Best Practices

1. **Завжди вказуйте екстрені контакти**
   ```python
   # Переконайтесь, що у кожного пацієнта є хоча б один екстрений контакт
   if not patient.contact_person_ids.filtered('is_emergency_contact'):
       # Сповістити користувача
   ```

2. **Використовуйте правильний тип відносин**
   ```python
   # Вибирайте найбільш відповідний тип
   contact.relationship = 'spouse'  # Для подружжя
   ```

3. **Додавайте корисні примітки**
   ```python
   contact.notes = "Available weekdays 9-17. Prefers phone calls."
   ```

4. **Архівуйте неактуальні контакти**
   ```python
   # Замість видалення, архівуйте
   contact.active = False
   ```

## Інтеграція з іншими модулями

### З Patient:
```python
# Доступ до контактів через пацієнта
patient = self.env['hr.hospital.patient'].browse(patient_id)
for contact in patient.contact_person_ids:
    print(f"{contact.full_name} ({contact.relationship})")
```

### Можливості розширення:
- Додати сповіщення для екстрених контактів
- Інтегрувати з системою SMS/Email
- Додати історію комунікацій
- Додати перевірку доступності контакту

## Автор

**Khatrus Zakhar**  
GitHub: https://github.com/zhatrus
