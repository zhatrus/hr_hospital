from odoo import fields, models


class HrHospitalDoctorSpecialization(models.Model):
    """Спеціальність лікаря"""
    _name = 'hr.hospital.doctor.specialization'
    _description = 'Doctor Specialization'
    _order = 'name'

    name = fields.Char(
        required=True,
        translate=True,
        help='Name of the medical specialization',
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

    def _compute_doctor_count(self):
        """Обчислює кількість лікарів за спеціальністю"""
        for record in self:
            record.doctor_count = len(record.doctor_ids)
