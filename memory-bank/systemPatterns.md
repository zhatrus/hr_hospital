# System Patterns - auto_monitoring

## Архітектура
Модульна архітектура Odoo з підключенням до зовнішньої БД:
- models (Python) - з psycopg2 для зовнішньої БД
- views (XML) - list/form/kanban/pivot
- security/data
- static/description

## Ключові компоненти
- **auto.monitoring.vehicle** - транспортні засоби (з vehicles)
- **auto.monitoring.tracker.data** - GPS дані (з tracker_light)
- **auto.monitoring.fuel.transaction** - заправки (з fuel_transactions)
- **auto.monitoring.trip** - поїздки (computed з tracker_data)
- **auto.monitoring.config** - налаштування підключення БД

## Патерни розробки
- Transient models для зовнішніх даних (не зберігаються в Odoo БД)
- Підключення через psycopg2 з connection pooling
- Кешування даних через computed fields
- Конфіг через ir.config_parameter

## Data Flow
Зовнішня PostgreSQL БД -> psycopg2 -> Odoo models (transient) -> Views
Конфіг: ir.config_parameter -> models -> psycopg2 connection
