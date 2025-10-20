some text# Hospital Management (hr_hospital)

## 🎯 Мета
Модуль **hr_hospital** призначений для автоматизації обліку в лікарнях: ведення даних про лікарів, пацієнтів, види захворювань та відвідування (візити) пацієнтів.

---

## 🧩 Основні можливості
- Облік **лікарів**, **пацієнтів**, **захворювань** і **візитів**.
- Окреме меню **"Лікарня"** з підменю:
  - **Пацієнти**
  - **Лікарі**
  - **Захворювання**
  - **Візити**
- Для кожної моделі створено представлення **Tree** та **Form**.
- Повні права доступу до моделей надано групі користувачів `base.group_user`.

---

## 🗂️ Структура модуля
hr_hospital/
│
├── models/
│ ├── hr_hospital_doctor.py
│ ├── hr_hospital_patient.py
│ ├── hr_hospital_disease.py
│ └── hr_hospital_visit.py
│
├── views/
│ ├── hr_hospital_doctor_views.xml
│ ├── hr_hospital_patient_views.xml
│ ├── hr_hospital_disease_views.xml
│ ├── hr_hospital_visit_views.xml
│ └── hr_hospital_menu.xml
│
├── data/
│ └── hr_hospital_disease_data.xml
│
├── demo/
│ ├── hr_hospital_doctor_demo.xml
│ └── hr_hospital_patient_demo.xml
│
├── security/
│ └── ir.model.access.csv
│
└── manifest.py

yaml
Копіювати код

---

## 📋 Дані
### Майстер-дані (`data/hr_hospital_disease_data.xml`)
- 3 записи для **моделі захворювань**

### Демо-дані (`demo/`)
- 3 записи для **лікарів**
- 3 записи для **пацієнтів**

---

## 🔒 Права доступу
Усі користувачі з групи `base.group_user` мають повний доступ до моделей:
- `hr.hospital.doctor`
- `hr.hospital.patient`
- `hr.hospital.disease`
- `hr.hospital.visit`

---

## 🧠 Технічні вимоги
- Odoo **17.0**
- Модуль залежить від:
  - `base`

---

## ✅ Критерії перевірки
- Модуль встановлюється без помилок.
- Дотримано структуру та іменування файлів.
- Лінтери (`flake8`, `pylint-odoo`) проходять без помилок.
- Модуль доступний у відкритому GitHub-репозиторії:  
  🔗 [https://github.com/zhatrus/hr_hospital](https://github.com/zhatrus/hr_hospital)

---

## 👨‍💻 Автор
**zhatrus**  
📧 [https://github.com/zhatrus](https://github.com/zhatrus)