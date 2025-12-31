{
    'name': 'Fleet Monitoring System',
    'version': '17.0.1.0.0',
    'category': 'Fleet',
    'summary': 'Система моніторингу автопарку з GPS-трекерами',
    'description': """
Fleet Monitoring System - Система моніторингу автопарку
========================================================

Модуль для моніторингу автопарку з підключенням до зовнішньої PostgreSQL БД.

🚗 Основні можливості:
----------------------
* **Дашборд**: статистика по ТЗ, пробігу, паливу, порушенням
* **Моніторинг**: список ТЗ з поточним статусом та швидкістю
* **Поїздки**: журнал поїздок з маршрутами та пробігом
* **Паливо**: облік заправок, витрати, залишків
* **Звіти**: пробіг, паливо, порушення швидкості
* **Налаштування**: ТЗ, сповіщення, користувачі

📊 Зовнішня БД:
---------------
* tracker_light - GPS дані трекерів
* fuel_transactions - паливні транзакції
* vehicles - транспортні засоби

🇺🇦 Українська локалізація:
---------------------------
Повністю перекладений інтерфейс.

Автор: Khatrus Zakhar
Ліцензія: LGPL-3
""",
    'author': 'Khatrus Zakhar',
    'maintainer': 'Khatrus Zakhar',
    'website': 'https://github.com/zhatrus/auto_monitoring',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
    ],
    'external_dependencies': {
        'python': ['psycopg2'],
    },
    'data': [
        'security/auto_monitoring_groups.xml',
        'security/ir.model.access.csv',

        'data/ir_config_parameter_data.xml',

        'views/auto_monitoring_vehicle_views.xml',
        'views/auto_monitoring_tracker_views.xml',
        'views/auto_monitoring_fuel_views.xml',
        'views/auto_monitoring_trip_views.xml',
        'views/auto_monitoring_config_views.xml',
        'views/auto_monitoring_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'auto_monitoring/static/src/css/auto_monitoring.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [
        'static/description/icon.png'
    ],
}
