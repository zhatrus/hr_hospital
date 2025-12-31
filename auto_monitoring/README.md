# Fleet Monitoring System

Система моніторингу автопарку для Odoo 17 з підключенням до зовнішньої PostgreSQL бази даних GPS-трекерів та паливних карток.

## Можливості

- **Дашборд** — статистика по ТЗ, пробігу, паливу, порушенням
- **Моніторинг** — відстеження позицій всіх ТЗ в реальному часі
- **Поїздки** — автоматичний розрахунок на основі GPS-даних
- **Паливо** — облік заправок та аналітика витрати
- **Звіти** — pivot та graph аналітика

## Зовнішня база даних

Модуль працює з такими таблицями PostgreSQL:

| Таблиця | Опис |
|---------|------|
| `vehicles` | Транспортні засоби (IMEI, держ.номер, модель) |
| `tracker_light` | GPS дані (координати, швидкість, паливо) |
| `fuel_transactions` | Транзакції з паливних карток |

## Встановлення

1. Скопіюйте модуль в папку addons
2. Встановіть залежність:
   ```bash
   pip install psycopg2-binary
   ```
3. Оновіть список модулів в Odoo
4. Встановіть модуль "Fleet Monitoring System"

## Налаштування підключення

### Через інтерфейс Odoo

Налаштування → Fleet Monitor → Підключення до БД

### Через odoo.conf

```ini
[options]
auto_monitoring_db_host = 192.168.1.100
auto_monitoring_db_port = 5432
auto_monitoring_db_name = monitoring
auto_monitoring_db_user = lynx
auto_monitoring_db_password = your_password
```

### Через ir.config_parameter

Параметри системи:
- `auto_monitoring.db_host`
- `auto_monitoring.db_port`
- `auto_monitoring.db_name`
- `auto_monitoring.db_user`
- `auto_monitoring.db_password`
- `auto_monitoring.speed_limit` (за замовчуванням 130 км/год)

## Використання

1. **Синхронізація ТЗ**: Моніторинг → Транспортні засоби → Action → "Синхронізувати ТЗ"
2. **Оновлення позицій**: Моніторинг → Транспортні засоби → Action → "Оновити позиції"
3. **Синхронізація поїздок**: Поїздки → Action → "Синхронізувати поїздки"

## Групи доступу

| Група | Права |
|-------|-------|
| User | Перегляд даних |
| Manager | Керування ТЗ та звіти |
| Administrator | Повний доступ + налаштування БД |

## Структура модуля

```
auto_monitoring/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── ir_config_parameter_data.xml
├── models/
│   ├── __init__.py
│   ├── db_connector.py
│   ├── auto_monitoring_vehicle.py
│   ├── auto_monitoring_tracker.py
│   ├── auto_monitoring_fuel.py
│   ├── auto_monitoring_trip.py
│   └── res_config_settings.py
├── security/
│   ├── auto_monitoring_groups.xml
│   └── ir.model.access.csv
├── static/
│   ├── description/
│   │   ├── icon.png
│   │   └── index.html
│   └── src/
│       └── css/
│           └── auto_monitoring.css
└── views/
    ├── auto_monitoring_vehicle_views.xml
    ├── auto_monitoring_tracker_views.xml
    ├── auto_monitoring_fuel_views.xml
    ├── auto_monitoring_trip_views.xml
    ├── auto_monitoring_config_views.xml
    └── auto_monitoring_menu.xml
```

## Технічні вимоги

- Odoo 17.0
- Python 3.10+
- psycopg2-binary
- PostgreSQL (зовнішня БД)

## Автор

Khatrus Zakhar

## Ліцензія

LGPL-3
