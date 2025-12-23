# Active Context

## Поточна задача
Завершено виправлення технічних боргів та помилок завантаження:
- Виправлено дублікати XML ID та полів.
- Виправлено застарілі XML теги (`<data>`).
- Виправлено помилки лінтера (Pylint/Flake8) в Python коді.
- Виправлено критичну помилку завантаження прав доступу (`ir.model.access.csv`).

Покращити UI для моделі "Пацієнт" (hr.hospital.patient):
- smart buttons для історії візитів та діагнозів
- швидке створення візиту з картки пацієнта
- вкладка з історією діагнозів (лікар + дата)
- пошук пацієнта по ПІБ або телефону

Додатково: виправити помилку OwlError у Pivot/Calendar (домен фільтра "This Month") та зробити читабельний заголовок події в календарі для Visit.

Також: покращити UI для моделі "Лікар" (hr.hospital.doctor): form (ментор/інтерни), search (фільтри Mentors/Interns), kanban (групування по спеціальностях + quick visit).

Також: додати аналітику та звіти:
- Diagnosis: pivot/graph (захворюваність) + demo дані.
- Diseases: searchpanel з ієрархічним вибором.
- Wizard: звіт по діагнозах за період (фільтри лікар/хвороба/дати) з запуском з Print меню лікаря.

## Останні зміни
- [x] **FIX**: Виправлено помилку завантаження модуля (відсутні зовнішні ID груп в CSV).
- [x] **FIX**: Виправлено дублювання XML ID в action/search views для Doctor та Patient.
- [x] **FIX**: Виправлено дублювання поля `visit_date` в `hr_hospital_diagnosis_views.xml`.
- [x] **FIX**: Прибрано застарілі теги `<data>` в security XML файлах.
- [x] **FIX**: Pylint fixes: docstrings, naming conventions, protected access.
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
- [x] Diagnosis: додано disease_type_id (stored) + pivot/graph views, action, menu Reports.
- [x] Diagnosis: додано demo файл з 6 діагнозами та підключено в __manifest__.
- [x] Diseases: додано searchpanel (hierarchize по parent_id) + підв'язано search view до action.
- [x] Wizard: оновлено disease.report.wizard під звіт по діагнозах за період + запуск з Print меню Doctor (list/form).

## Наступні кроки
- [ ] Upgrade модуль hr_hospital та перевірити: Patient form (кнопки/вкладки), search, швидке створення Visit.
- [ ] Перевірити: Visits Pivot (This Month) та Calendar — чи зник OwlError і чи заголовок події став читабельний.
- [ ] Перевірити: Doctors — kanban (групування по specialization, кнопка Quick Visit), form (Mentor/Interns), search (Mentors/Interns).
- [ ] Перевірити: Reports -> Disease Incidence (pivot/graph) для діагнозів.
- [ ] Перевірити: Diseases list -> searchpanel (ієрархія).
- [ ] Перевірити: Doctors -> Print -> Disease Report (візард + результат згрупований по хворобах).

## Відкриті питання
- [ ] За потреби додати ще демо-дані/діагнози під нові demo visits.
