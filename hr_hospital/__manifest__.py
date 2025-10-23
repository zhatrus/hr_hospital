{
    'name': 'Hospital Management',
    'version': '17.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Hospital management system for doctors and patients',
    'description': 'A simple hospital management system.',
    'author': 'Khatrus Zakhar',
    'website': 'https://github.com/zhatrus/hr_hospital',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/hr_hospital_disease_data.xml',

        'views/hr_hospital_doctor_views.xml',
        'views/hr_hospital_patient_views.xml',
        'views/hr_hospital_disease_views.xml',
        'views/hr_hospital_visit_views.xml',
        'views/hr_hospital_menu.xml',
    ],
    'demo': [
        'demo/hr_hospital_doctor_demo.xml',
        'demo/hr_hospital_patient_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [
        'static/description/icon.png'
    ],
}
