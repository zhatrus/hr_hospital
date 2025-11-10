{
    'name': 'Hospital Management',
    'version': '17.0.2.3.1',
    'category': 'Healthcare',
    'summary': 'Hospital management system for doctors and patients',
    'author': 'Khatrus Zakhar',
    'website': 'https://github.com/zhatrus/hr_hospital',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',

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

        'wizard/mass_reassign_doctor_wizard_views.xml',
        'wizard/disease_report_wizard_views.xml',
        'wizard/reschedule_visit_wizard_views.xml',
        'wizard/doctor_schedule_wizard_views.xml',
        'wizard/patient_card_export_wizard_views.xml',
    ],
    'demo': [
        'demo/hr_hospital_doctor_specialization_demo.xml',
        'demo/hr_hospital_doctor_demo.xml',
        'demo/hr_hospital_patient_demo.xml',
        'demo/hr_hospital_contact_person_demo.xml',
        'demo/hr_hospital_disease_demo.xml',
        'demo/hr_hospital_visit_demo.xml',
        'demo/hr_hospital_diagnosis_demo.xml',
        'demo/hr_hospital_doctor_schedule_demo.xml',
        'demo/hr_hospital_patient_doctor_history_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [
        'static/description/icon.png'
    ],
}
