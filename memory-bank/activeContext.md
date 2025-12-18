# Active Context

## Поточна задача
Покращити UI для моделі "Пацієнт" (hr.hospital.patient):
- smart buttons для історії візитів та діагнозів
- швидке створення візиту з картки пацієнта
- вкладка з історією діагнозів (лікар + дата)
- пошук пацієнта по ПІБ або телефону

Додатково: виправити помилку OwlError у Pivot/Calendar (домен фільтра "This Month") та зробити читабельний заголовок події в календарі для Visit.

Також: покращити UI для моделі "Лікар" (hr.hospital.doctor): form (ментор/інтерни), search (фільтри Mentors/Interns), kanban (групування по спеціальностях + quick visit).

## Останні зміни
- [x] Patient form: додано smart buttons Visits/Diagnoses + кнопку "New Visit".
- [x] Patient form: вкладка Visits оновлена під нові поля (scheduled_date/status/visit_type).
- [x] Patient form: вкладка Diagnoses (read-only) з історією діагнозів.
- [x] Patient model: додано actions для відкриття історії Visits/Diagnoses та швидкого створення Visit.
- [x] Patient search: пошук одним рядком по ПІБ або телефону.
- [x] Visit search: прибрано datetime.timedelta з доменів (Today/This Week/This Month/Last 30 Days), щоб не падали Pivot/Calendar.
- [x] Visit calendar: додано name_get для читабельного підпису події (замість hr.hospital.visit,ID).
- [x] Doctor form: додано блок "Mentor" для інтернів + вкладку Interns у вигляді kanban.
- [x] Doctor search: додано фільтри Mentors/Interns та підв'язано search view до action.
- [x] Doctor kanban: додано представлення з кнопкою "Quick Visit" та дефолтним group_by по specialization.
- [x] Doctor demo: додано 2 додаткових інтерни.

## Наступні кроки
- [ ] Upgrade модуль hr_hospital та перевірити: Patient form (кнопки/вкладки), search, швидке створення Visit.
- [ ] Перевірити: Visits Pivot (This Month) та Calendar — чи зник OwlError і чи заголовок події став читабельний.
- [ ] Перевірити: Doctors — kanban (групування по specialization, кнопка Quick Visit), form (Mentor/Interns), search (Mentors/Interns).

## Відкриті питання
- [ ] За потреби додати ще демо-дані/діагнози під нові demo visits.
