# Tech Context - auto_monitoring

## Технології
- **Backend**: Odoo 17.0 (Python 3.10+)
- **Frontend**: Odoo Web (QWeb/OWL), XML views
- **Зовнішня БД**: PostgreSQL (psycopg2)
- **Карти**: Leaflet.js (через OWL widget)

## Залежності
- base
- web
- psycopg2-binary (Python package)

## Зовнішня БД
Таблиці:
- `tracker_light` - GPS дані трекерів
- `fuel_transactions` - паливні транзакції
- `vehicles` - транспортні засоби

## Конфігурації
**Налаштування підключення** (ir.config_parameter):
- `auto_monitoring.db_host` - IP адреса сервера
- `auto_monitoring.db_port` - порт (5432)
- `auto_monitoring.db_name` - назва бази
- `auto_monitoring.db_user` - логін
- `auto_monitoring.db_password` - пароль

Або через `odoo.conf`:
```ini
[options]
auto_monitoring_db_host = 192.168.x.x
auto_monitoring_db_port = 5432
auto_monitoring_db_name = monitoring
auto_monitoring_db_user = lynx
auto_monitoring_db_password = ***
```
