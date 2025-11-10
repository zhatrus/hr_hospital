from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDoctorSpecialization(models.Model):
    """Спеціальність лікаря"""
    _name = 'hr.hospital.doctor.specialization'
    _description = 'Doctor Specialization'
    _order = 'name'
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)',
         'Specialization code must be unique!'),
    ]

    name = fields.Char(
        required=True,
        translate=True,
        help='Name of the medical specialization',
    )
    code = fields.Char(
        string='Specialization Code',
        size=10,
        required=True,
        help='Unique code for the specialization',
    )
    description = fields.Text(
        translate=True,
        help='Description of the specialization',
    )
    active = fields.Boolean(
        default=True,
    )
    doctor_ids = fields.One2many(
        comodel_name='hr.hospital.doctor',
        inverse_name='specialization_id',
        string='Doctors',
    )
    doctor_count = fields.Integer(
        compute='_compute_doctor_count',
        string='Number of Doctors',
    )

    @api.constrains('code')
    def _check_code(self):
        """Валідація коду спеціальності"""
        for record in self:
            if record.code and len(record.code) > 10:
                raise ValidationError(
                    _('Specialization code cannot exceed 10 characters!')
                )

    def _compute_doctor_count(self):
        """Обчислює кількість лікарів за спеціальністю"""
        for record in self:
            record.doctor_count = len(record.doctor_ids)
