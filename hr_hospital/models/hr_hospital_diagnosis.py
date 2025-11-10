from odoo import fields, models


class HrHospitalDiagnosis(models.Model):
    """Діагноз пацієнта під час візиту"""
    _name = 'hr.hospital.diagnosis'
    _description = 'Patient Diagnosis'
    _order = 'visit_id, sequence, id'

    visit_id = fields.Many2one(
        comodel_name='hr.hospital.visit',
        string='Visit',
        required=True,
        ondelete='cascade',
        index=True,
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease',
        required=True,
        help='Diagnosed disease',
    )
    diagnosis_type = fields.Selection(
        selection=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('complication', 'Complication'),
        ],
        default='primary',
        required=True,
    )
    sequence = fields.Integer(
        default=10,
        help='Sequence order for display',
    )
    description = fields.Text(
        help='Additional details about the diagnosis',
    )
    active = fields.Boolean(
        default=True,
    )
