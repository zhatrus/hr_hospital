from odoo import fields, models
from odoo import fields, models


class HrHospitalDisease(models.Model):
    _name = 'hr.hospital.disease'
    _description = 'Hospital Disease'

    name = fields.Char(
        string='Disease Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    code = fields.Char(
        string='Disease Code',
    )
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='disease_id',
        string='Visits',
    )

class HrHospitalDisease(models.Model):
    _name = 'hr.hospital.disease'
    _description = 'Hospital Disease'

    name = fields.Char(
        string='Disease Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    code = fields.Char(
        string='Disease Code',
    )
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='disease_id',
        string='Visits',
    )