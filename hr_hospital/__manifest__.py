{
    'name': 'Hospital Management System',
    'version': '17.0.3.0.2',
    'category': 'Healthcare',
    'summary': 'Професійна система управління медичним закладом з повною українською локалізацією',
    'description': """
Hospital Management System - Професійне рішення для медичних закладів
=====================================================================

Повнофункціональна система управління лікарнею для Odoo 17 з повною українською локалізацією.

🏥 Основні можливості:
----------------------
* **Управління пацієнтами**: повний облік з історією, контактними особами, групами крові, алергіями
* **База лікарів**: спеціалізації, ліцензії, графіки роботи, менторство інтернів, рейтинги
* **Візити та діагнози**: планування, множинні діагнози, рекомендації, вартість послуг
* **Класифікатор хвороб**: ієрархічна структура з кодами МКХ-10, ступенями небезпеки
* **Звіти та аналітика**: pivot-таблиці, графіки, експорт у JSON/CSV
* **Безпека**: 5 рівнів доступу (пацієнт, інтерн, лікар, менеджер, адміністратор)
* **Візарди**: масове перепризначення лікарів, перенесення візитів, автозаповнення розкладу
* **Валідація**: SQL та Python обмеження для цілісності даних
* **Локалізація**: 350+ перекладів українською мовою

📊 Технічні особливості:
------------------------
* Повне покриття unit-тестами
* Record rules для розмежування доступу
* Computed fields з кешуванням
* Constraints для валідації даних
* Інтеграція з mail.thread для відстеження змін
* Друковані звіти з QWeb шаблонами

🇺🇦 Українська локалізація:
---------------------------
Повністю перекладений інтерфейс, повідомлення про помилки, підказки та всі елементи системи.

Автор: Khatrus Zakhar
Ліцензія: LGPL-3
""",
    'author': 'Khatrus Zakhar',
    'maintainer': 'Khatrus Zakhar',
    'website': 'https://github.com/zhatrus/hr_hospital',
    'support': 'https://github.com/zhatrus/hr_hospital/issues',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        'security/hr_hospital_groups.xml',
        'security/ir.model.access.csv',
        'security/hr_hospital_record_rules.xml',

        'data/hr_hospital_disease_data.xml',

        'views/hr_hospital_doctor_specialization_views.xml',
        'views/hr_hospital_doctor_schedule_views.xml',
        'views/hr_hospital_doctor_views.xml',
        'views/hr_hospital_patient_views.xml',
        'views/hr_hospital_contact_person_views.xml',
        'views/hr_hospital_disease_views.xml',
        'views/hr_hospital_diagnosis_views.xml',
        'views/hr_hospital_visit_views.xml',
        'views/hr_hospital_search_filters.xml',
        'views/hr_hospital_menu.xml',

        'report/hr_hospital_doctor_report.xml',
        'report/hr_hospital_doctor_report_template.xml',

        'wizard/mass_reassign_doctor_wizard_views.xml',
        'wizard/disease_report_wizard_views.xml',
        'wizard/reschedule_visit_wizard_views.xml',
        'wizard/doctor_schedule_wizard_views.xml',
        'wizard/patient_card_export_wizard_views.xml',
    ],
    'demo': [
        'demo/res_company_demo.xml',
        'demo/hr_hospital_doctor_specialization_demo.xml',
        'demo/hr_hospital_doctor_demo.xml',
        'demo/hr_hospital_doctor_demo_extended.xml',
        'demo/hr_hospital_patient_demo.xml',
        'demo/hr_hospital_patient_demo_extended.xml',
        'demo/hr_hospital_contact_person_demo.xml',
        'demo/hr_hospital_visit_demo.xml',
        'demo/hr_hospital_diagnosis_demo_6.xml',
        # TODO: Fix IDs in these files
        # 'demo/hr_hospital_disease_demo.xml',
        # 'demo/hr_hospital_diagnosis_demo.xml',
        # 'demo/hr_hospital_doctor_schedule_demo.xml',
        # 'demo/hr_hospital_patient_doctor_history_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [
        'static/description/icon.png'
    ],
}
