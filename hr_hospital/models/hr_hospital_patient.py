from odoo import fields, models


class HrHospitalPatient(models.Model):
    _name = 'hr.hospital.patient'
    _description = 'Hospital Patient'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'

    # Успадковані поля з abstract.person:
    # - last_name, first_name, middle_name
    # - phone, email
    # - gender, date_of_birth
    # - age (computed), full_name (computed)
    # - country_id, lang_id
    # - image fields (з image.mixin)

    # Специфічні поля для пацієнта
    address = fields.Text(
        string='Address',
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Attending Doctor',
    )
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='patient_id',
        string='Visits',
    )
