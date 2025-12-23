# Progress

## Що зроблено
- [x] **Технічні виправлення**: Pylint/Flake8, duplicate XML IDs, deprecated XML tags, Access CSV module loading error.
- [x] Виправлено верстку Address/Allergies в картці пацієнта.
- [x] Виправлено верстку у wizard-вікнах з `nolabel` (Mass Reassign Doctor, Reschedule Visit).
- [x] Піднято версію модуля і доповнено `__manifest__.py`.
- [x] Додано `static/description/index.html`.
- [x] Visit: оновлено form view (statusbar + додаткові поля).
- [x] Visit: додано calendar view і підключено до action.
- [x] Visit: search view доповнено фільтром "This Month" (та є group by status).
- [x] Visit: додано pivot view + action для поточного місяця + пункт меню в Reports.
- [x] Visit: demo дані — додано 4-й demo запис.
- [x] Visit: виправлено домени date filters (прибрано datetime.timedelta), щоб не падав OwlError у Pivot/Calendar.
- [x] Visit: покращено назву події в календарі (name_get замість hr.hospital.visit,ID).
- [x] Patient: додано smart buttons Visits/Diagnoses та кнопку швидкого створення Visit.
- [x] Patient: додано вкладку Diagnoses (історія діагнозів лікарів).
- [x] Patient: search view з пошуком по ПІБ або телефону (одним рядком).
- [x] Doctor: form view доповнено блоком Mentor (для інтернів) та списком Interns у вигляді kanban.
- [x] Doctor: search view доповнено фільтрами Mentors/Interns.
- [x] Doctor: додано kanban view з групуванням по specialization та кнопкою швидкого створення Visit.
- [x] Doctor: demo дані — додано 2 додаткових записи типу Intern.
- [x] Diagnosis: додано disease_type_id (stored) + pivot/graph views, action та пункт меню в Reports.
- [x] Diagnosis: додано demo файл з 6 діагнозами та підключено в __manifest__.
- [x] Diseases: додано searchpanel (hierarchize по parent_id) + підв'язано search view до action.
- [x] Wizard: звіт по діагнозах за період (doctor_ids/disease_ids/date_from/date_to) + запуск з Print меню Doctor (list/form).

## Що в процесі
- [ ] Перевірка після Upgrade модуля на стенді.

## Що залишилось
- [ ] За потреби аналогічно виправити інші в’юхи.
- [ ] За потреби додати більше demo даних під нові представлення.

## Блокери
- Немає.
