from odoo import api, fields, models


class HrHospitalDoctor(models.Model):
    _name = 'hr.hospital.doctor'
    _description = 'Hospital Doctor'

    name = fields.Char(
        string='Full Name',
        required=True,
    )
    specialization = fields.Char(
        string='Specialization',
    )
    phone = fields.Char(
        string='Phone',
    )
    email = fields.Char(
        string='Email',
    )
    is_intern = fields.Boolean(
        string='Is Intern',
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