# 🚀 Команди для деплою модуля auto_monitoring

## 📥 Оновлення коду з GitHub

```bash
cd ~/odoo/repositories/zhatrus/hr_hospital/
git pull
```

## 🔍 Перевірка якості коду

```bash
cd ~/odoo
source venv/bin/activate
cd ~/odoo/custom_addons/auto_monitoring
pylint .
flake8 .
deactivate
```

## 🔄 Оновлення модуля в Odoo

```bash
cd ~/odoo
odoo-helper addons update-list
odoo-helper addons update auto_monitoring -d test17
odoo-helper restart
```

---

## 🧪 Запуск тестів

```bash
cd ~/odoo
source venv/bin/activate

# Запустити всі тести модуля
odoo -d test17 -i auto_monitoring --test-enable --stop-after-init

# Запустити тільки тести auto_monitoring
odoo -d test17 --test-tags auto_monitoring --stop-after-init

# Запустити конкретний тестовий клас
odoo -d test17 --test-tags /auto_monitoring/tests/test_auto_monitoring_models.py:TestAutoMonitoringModels --stop-after-init

deactivate
```

---

## 🔧 Альтернативні команди

### Деінсталяція та встановлення заново

```bash
cd ~/odoo
odoo-helper addons uninstall auto_monitoring -d test17
odoo-helper addons install auto_monitoring -d test17
odoo-helper restart
```

### Перевірка логів

```bash
# Знайти лог-файл
ps aux | grep odoo

# Або подивитись конфіг
cat ~/.odoo-helper.conf | grep log

# Або запустити з виводом помилок
cd ~/odoo
odoo-helper addons update auto_monitoring -d test17 2>&1 | tee update.log
```

---

## 📊 Швидка перевірка після деплою

1. **Відкрити Odoo**: http://your-server:8069
2. **Перейти в Apps** → знайти "Fleet Monitoring System"
3. **Перевірити меню**:
   - Fleet Monitor → Поїздки
   - Fleet Monitor → Налаштування → Мети поїздок
4. **Синхронізувати дані**:
   - Налаштування → Мети поїздок → Action "Синхронізувати мети поїздок"
5. **Перевірити поїздки**:
   - Відкрити поїздку
   - Заповнити мету та коментар
   - Зберегти

---

## ⚠️ Troubleshooting

### Модуль не встановлюється

```bash
# Подивитись детальний лог
cd ~/odoo
source venv/bin/activate
odoo -i auto_monitoring -d test17 --stop-after-init --log-level=debug 2>&1 | grep -A 50 "ERROR\|Traceback"
deactivate
```

### Видалити старі дані (якщо потрібно)

```bash
# Підключитись до БД
sudo -u postgres psql -d test17

# Видалити таблицю (якщо є проблеми з міграцією)
DROP TABLE IF EXISTS auto_monitoring_trip CASCADE;

# Вийти
\q
```

### Перезапустити Odoo

```bash
cd ~/odoo
odoo-helper restart
```

---

## 📝 Примітки

- Завжди робити `git pull` перед оновленням
- Перевіряти `pylint` та `flake8` перед комітом
- Після оновлення перевіряти логи на помилки
- Тести запускати локально перед деплоєм на сервер
