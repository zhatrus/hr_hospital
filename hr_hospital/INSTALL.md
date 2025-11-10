# Інструкція з встановлення та оновлення модуля HR Hospital

## Нове встановлення

### 1. Копіювання модуля

Скопіюйте директорію `hr_hospital` до папки з аддонами Odoo:

```bash
cp -r hr_hospital /path/to/odoo/addons/
```

### 2. Оновлення списку модулів

У Odoo перейдіть до:
- **Apps** → **Update Apps List**

### 3. Встановлення модуля

Знайдіть модуль "Hospital Management" у списку Apps і натисніть **Install**.

---

## Оновлення з версії 17.0.1.0.0 до 17.0.2.0.0

### ⚠️ ВАЖЛИВО: Backup бази даних

Перед оновленням обов'язково створіть резервну копію бази даних:

```bash
pg_dump your_database > backup_before_upgrade.sql
```

### Зміни у структурі даних

Версія 17.0.2.0.0 містить **breaking changes**:

#### Видалені поля:
- `hr.hospital.doctor.name`
- `hr.hospital.patient.name`

#### Додані поля:
- `last_name` (Char, required) - Прізвище
- `first_name` (Char, required) - Ім'я
- `middle_name` (Char) - По батькові
- `full_name` (Char, computed, stored) - Повне ім'я
- `gender` (Selection) - Стать
- `date_of_birth` (Date) - Дата народження
- `age` (Integer, computed, stored) - Вік
- `country_id` (Many2one) - Країна громадянства
- `lang_id` (Many2one) - Мова спілкування
- Поля для зображень (image_1920, image_1024, тощо)

### Кроки оновлення

#### 1. Зупиніть Odoo сервер

```bash
sudo systemctl stop odoo
# або
pkill -f odoo-bin
```

#### 2. Створіть SQL скрипт для міграції даних

Створіть файл `migrate_hr_hospital.sql`:

```sql
-- Додаємо нові колонки
ALTER TABLE hr_hospital_doctor 
ADD COLUMN IF NOT EXISTS last_name VARCHAR,
ADD COLUMN IF NOT EXISTS first_name VARCHAR,
ADD COLUMN IF NOT EXISTS middle_name VARCHAR;

ALTER TABLE hr_hospital_patient 
ADD COLUMN IF NOT EXISTS last_name VARCHAR,
ADD COLUMN IF NOT EXISTS first_name VARCHAR,
ADD COLUMN IF NOT EXISTS middle_name VARCHAR;

-- Міграція даних для лікарів
-- Припускаємо формат: "Прізвище Ім'я" або "Прізвище Ім'я По батькові"
UPDATE hr_hospital_doctor 
SET 
    last_name = split_part(name, ' ', 1),
    first_name = split_part(name, ' ', 2),
    middle_name = CASE 
        WHEN array_length(string_to_array(name, ' '), 1) > 2 
        THEN split_part(name, ' ', 3) 
        ELSE NULL 
    END
WHERE name IS NOT NULL;

-- Міграція даних для пацієнтів
UPDATE hr_hospital_patient 
SET 
    last_name = split_part(name, ' ', 1),
    first_name = split_part(name, ' ', 2),
    middle_name = CASE 
        WHEN array_length(string_to_array(name, ' '), 1) > 2 
        THEN split_part(name, ' ', 3) 
        ELSE NULL 
    END
WHERE name IS NOT NULL;
```

#### 3. Виконайте SQL скрипт

```bash
psql -U odoo_user -d your_database -f migrate_hr_hospital.sql
```

#### 4. Оновіть код модуля

```bash
cd /path/to/odoo/addons/
rm -rf hr_hospital
cp -r /path/to/new/hr_hospital .
```

#### 5. Оновіть модуль через Odoo CLI

```bash
odoo-bin -u hr_hospital -d your_database --stop-after-init
```

#### 6. Запустіть Odoo сервер

```bash
sudo systemctl start odoo
# або
odoo-bin -c /path/to/odoo.conf
```

### Перевірка після оновлення

1. Перейдіть до **Hospital** → **Doctors**
2. Відкрийте будь-якого лікаря
3. Перевірте, що:
   - Поля `last_name`, `first_name` заповнені
   - Поле `full_name` відображається правильно
   - Можна додати аватар

4. Повторіть для пацієнтів: **Hospital** → **Patients**

### Ручне виправлення даних (якщо потрібно)

Якщо автоматична міграція не спрацювала ідеально, ви можете вручну виправити дані:

1. Відкрийте запис
2. Відредагуйте поля `last_name`, `first_name`, `middle_name`
3. Збережіть
4. Поле `full_name` оновиться автоматично

---

## Розробка та налагодження

### Встановлення у режимі розробки

```bash
odoo-bin -c odoo.conf -d your_database -i hr_hospital --dev=all
```

### Оновлення у режимі розробки

```bash
odoo-bin -c odoo.conf -d your_database -u hr_hospital --dev=all
```

### Перевірка коду

#### Python код (flake8)
```bash
flake8 hr_hospital/ --exclude=__pycache__
```

#### Python код (pylint-odoo)
```bash
pylint --load-plugins=pylint_odoo hr_hospital/
```

---

## Тестування модуля

### 1. Створення нового лікаря

```python
doctor = self.env['hr.hospital.doctor'].create({
    'last_name': 'Smith',
    'first_name': 'John',
    'middle_name': 'Michael',
    'email': 'john.smith@hospital.com',
    'phone': '+380501234567',
    'gender': 'male',
    'date_of_birth': '1980-05-15',
    'specialization': 'Cardiology',
})

# Перевірте автоматичні обчислення
assert doctor.full_name == 'Smith John Michael'
assert doctor.age > 0
```

### 2. Тестування валідації

```python
# Невірний email
try:
    doctor = self.env['hr.hospital.doctor'].create({
        'last_name': 'Test',
        'first_name': 'Test',
        'email': 'invalid-email',  # Помилковий формат
    })
except ValidationError:
    print("Валідація email працює!")

# Невірний телефон
try:
    doctor = self.env['hr.hospital.doctor'].create({
        'last_name': 'Test',
        'first_name': 'Test',
        'phone': '123',  # Помилковий формат
    })
except ValidationError:
    print("Валідація телефону працює!")
```

---

## Вирішення проблем

### Проблема: Модуль не встановлюється

**Рішення:**
1. Перевірте логи Odoo: `tail -f /var/log/odoo/odoo.log`
2. Переконайтеся, що модуль `web` встановлений
3. Перевірте права доступу до файлів модуля

### Проблема: Старе поле 'name' не існує

**Рішення:**
Це очікувана поведінка після оновлення. Використовуйте:
- `full_name` - для читання повного імені
- `last_name`, `first_name`, `middle_name` - для редагування

### Проблема: ValidationError при збереженні

**Рішення:**
Перевірте формати:
- **Email**: повинен бути у форматі `example@domain.com`
- **Телефон**: повинен бути у міжнародному форматі `+380XXXXXXXXX`

---

## Контакти

При виникненні питань або проблем:
- GitHub: https://github.com/zhatrus/hr_hospital
- Email: через GitHub профіль

---

## Автор

**Khatrus Zakhar**  
Версія документа: 2025-11-09
