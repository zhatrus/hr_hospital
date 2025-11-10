from odoo import fields, models


class HrHospitalDoctor(models.Model):
    _name = 'hr.hospital.doctor'
    _description = 'Hospital Doctor'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'

    # Успадковані поля з abstract.person:
    # - last_name, first_name, middle_name
    # - phone, email
    # - gender, date_of_birth
    # - age (computed), full_name (computed)
    # - country_id, lang_id
    # - image fields (з image.mixin)

    # Специфічні поля для лікаря
    specialization = fields.Char(
    )
    is_intern = fields.Boolean(
        string='Is Intern Doctor',
        default=False,
    )
    mentor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Mentor Doctor',
        domain="[('is_intern', '=', False)]",
    )
    intern_ids = fields.One2many(
        comodel_name='hr.hospital.doctor',
        inverse_name='mentor_id',
        string='Interns',
    )
    patient_ids = fields.One2many(
        comodel_name='hr.hospital.patient',
        inverse_name='doctor_id',
        string='Patients',
    )
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='doctor_id',
        string='Visits',
    )
