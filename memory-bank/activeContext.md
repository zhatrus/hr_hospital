# Active Context

## Поточна задача
**Створення нового модуля `auto_monitoring`** - система моніторингу автопарку для Odoo 17.

Модуль має:
- Підключатися до зовнішньої PostgreSQL БД з GPS-трекерами та паливними транзакціями
- Відображати дані у стилі Odoo (list/form/kanban/pivot views)
- Надавати функціонал: Дашборд, Моніторинг на карті, Поїздки, Паливо, Звіти, Налаштування

## Зовнішня БД (PostgreSQL)
Таблиці:
- **tracker_light**: GPS дані (imei, lat/lon, speed, fuel, odometer, address, timestamp)
- **fuel_transactions**: Заправки (trans_id, card_num, volume, price, azs_name, trans_date)
- **vehicles**: Транспортні засоби (id, imei, reg_number, vehicle_model, fuel_card_number, fuel_norm)

Підключення: через конфіг Odoo або окремий файл параметрів (IP, port, dbname, user, password)

## Останні зміни
- [x] Проаналізовано demo.html з прикладом UI
- [x] Проаналізовано структуру hr_hospital як reference
- [x] Визначено структуру зовнішньої БД
- [x] Створено модуль auto_monitoring з повною структурою
- [x] Моделі: db_connector, vehicle, tracker, fuel, trip, res_config_settings
- [x] Views: vehicle, tracker, fuel, trip, config, menu
- [x] Security: groups, access.csv
- [x] Static: CSS, description/index.html, README.md

## Наступні кроки
1. Встановити модуль на Odoo сервері
2. Налаштувати підключення до зовнішньої БД (Settings → Fleet Monitor)
3. Натиснути "Перевірити підключення" для тестування
4. Синхронізувати транспортні засоби
5. Перевірити кожну вкладку окремо

## Відкриті питання
- [ ] Надати IP, port, dbname, user, password для зовнішньої БД
- [ ] Додати іконку модуля (icon.png) у static/description/
