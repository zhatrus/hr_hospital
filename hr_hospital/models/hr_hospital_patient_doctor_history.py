from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalPatientDoctorHistory(models.Model):
    """Історія зміни персональних лікарів пацієнта"""
    _name = 'hr.hospital.patient.doctor.history'
    _description = 'Patient Doctor Assignment History'
    _order = 'assignment_date desc'

    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True,
        ondelete='cascade',
        index=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
        ondelete='restrict',
    )
    assignment_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        index=True,
    )
    end_date = fields.Date(
        help='Date when this doctor assignment ended',
    )
    is_current = fields.Boolean(
        string='Current Assignment',
        compute='_compute_is_current',
        store=True,
    )
    notes = fields.Text(
        help='Reason for doctor change or additional notes',
    )

    @api.depends('end_date')
    def _compute_is_current(self):
        """Визначає чи є призначення поточним"""
        for record in self:
            record.is_current = not record.end_date

    @api.constrains('assignment_date', 'end_date')
    def _check_dates(self):
        """Перевірка коректності дат"""
        for record in self:
            if record.end_date and record.assignment_date:
                if record.end_date < record.assignment_date:
                    raise ValidationError(
                        _('End date cannot be earlier than '
                          'assignment date!')
                    )

    @api.constrains('patient_id', 'doctor_id', 'assignment_date')
    def _check_duplicate_assignment(self):
        """Перевірка на дублікати призначень на ту саму дату"""
        for record in self:
            duplicate = self.search([
                ('id', '!=', record.id),
                ('patient_id', '=', record.patient_id.id),
                ('doctor_id', '=', record.doctor_id.id),
                ('assignment_date', '=', record.assignment_date),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    _('This doctor is already assigned to this patient '
                      'on this date!')
                )
