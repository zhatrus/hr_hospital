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
        help='Date when doctor was assigned to patient',
    )
    change_date = fields.Date(
        help='Date when doctor was changed',
    )
    change_reason = fields.Text(
        help='Reason for changing the doctor',
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this assignment is currently active',
    )

    # Backward compatibility
    end_date = fields.Date(
        compute='_compute_end_date',
        store=True,
        help='Date when this doctor assignment ended (computed)',
    )
    is_current = fields.Boolean(
        string='Current Assignment',
        compute='_compute_is_current',
        store=True,
        help='Whether this is the current assignment (computed)',
    )
    notes = fields.Text(
        compute='_compute_notes',
        inverse='_inverse_notes',
        store=True,
        help='Reason for doctor change or additional notes',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure previous active assignments are closed when creating new."""
        for vals in vals_list:
            patient_id = vals.get('patient_id')
            if patient_id:
                prev_active = self.search([
                    ('patient_id', '=', patient_id),
                    ('is_active', '=', True),
                ])
                prev_active.write({
                    'change_date': vals.get(
                        'assignment_date', fields.Date.today()
                    ),
                    'is_active': False,
                })
        return super().create(vals_list)

    @api.depends('change_date')
    def _compute_end_date(self):
        """Обчислює end_date з change_date для зворотної сумісності"""
        for record in self:
            record.end_date = record.change_date

    @api.depends('is_active', 'change_date')
    def _compute_is_current(self):
        """Визначає чи є призначення поточним"""
        for record in self:
            record.is_current = record.is_active and not record.change_date

    @api.depends('change_reason')
    def _compute_notes(self):
        """Обчислює notes з change_reason для зворотної сумісності"""
        for record in self:
            record.notes = record.change_reason

    def _inverse_notes(self):
        """Зворотня функція для notes"""
        for record in self:
            record.change_reason = record.notes

    @api.constrains('assignment_date', 'change_date')
    def _check_dates(self):
        """Перевірка коректності дат"""
        for record in self:
            if record.change_date and record.assignment_date:
                if record.change_date < record.assignment_date:
                    raise ValidationError(
                        _('Change date cannot be earlier than '
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
