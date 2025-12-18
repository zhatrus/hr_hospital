# Active Context

## Поточна задача
Покращити UI для моделі "Пацієнт" (hr.hospital.patient):
- smart buttons для історії візитів та діагнозів
- швидке створення візиту з картки пацієнта
- вкладка з історією діагнозів (лікар + дата)
- пошук пацієнта по ПІБ або телефону

## Останні зміни
- [x] Patient form: додано smart buttons Visits/Diagnoses + кнопку "New Visit".
- [x] Patient form: вкладка Visits оновлена під нові поля (scheduled_date/status/visit_type).
- [x] Patient form: вкладка Diagnoses (read-only) з історією діагнозів.
- [x] Patient model: додано actions для відкриття історії Visits/Diagnoses та швидкого створення Visit.
- [x] Patient search: пошук одним рядком по ПІБ або телефону.

## Наступні кроки
- [ ] Upgrade модуль hr_hospital та перевірити: Patient form (кнопки/вкладки), search, швидке створення Visit.

## Відкриті питання
- [ ] За потреби додати ще демо-дані/діагнози під нові demo visits.
