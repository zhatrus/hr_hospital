from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDoctorSchedule(models.Model):
    """Графік роботи лікаря"""
    _name = 'hr.hospital.doctor.schedule'
    _description = 'Doctor Work Schedule'
    _order = 'doctor_id, date desc, day_of_week, time_from'

    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
        ondelete='cascade',
        index=True,
    )
    day_of_week = fields.Selection(
        selection=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
        ],
        string='Day of Week',
        help='Day of week for regular schedule',
    )
    date = fields.Date(
        string='Specific Date',
        help='Specific date for schedule (overrides day_of_week)',
    )
    time_from = fields.Float(
        string='Work From',
        required=True,
        help='Start time of work shift (in hours)',
    )
    time_to = fields.Float(
        string='Work To',
        required=True,
        help='End time of work shift (in hours)',
    )
    schedule_type = fields.Selection(
        selection=[
            ('working_day', 'Working Day'),
            ('vacation', 'Vacation'),
            ('sick_leave', 'Sick Leave'),
            ('conference', 'Conference'),
        ],
        default='working_day',
        required=True,
        help='Type of schedule entry',
    )
    notes = fields.Char(
        help='Additional notes about the schedule',
    )
    active = fields.Boolean(
        default=True,
    )

    @api.constrains('date', 'day_of_week')
    def _check_date_or_day(self):
        """Валідація: має бути або date, або day_of_week"""
        for record in self:
            if not record.date and not record.day_of_week:
                raise ValidationError(
                    _('Either Specific Date or Day of Week must be set!')
                )

    @api.constrains('time_from', 'time_to')
    def _check_work_time(self):
        """Валідація робочого часу"""
        for record in self:
            if record.time_from >= record.time_to:
                raise ValidationError(
                    _('Work end time must be later than start time!')
                )
            if record.time_from < 0 or record.time_from > 24:
                raise ValidationError(
                    _('Work start time must be between 0 and 24 hours!')
                )
            if record.time_to < 0 or record.time_to > 24:
                raise ValidationError(
                    _('Work end time must be between 0 and 24 hours!')
                )

    @api.constrains('doctor_id', 'day_of_week', 'date',
                    'time_from', 'time_to')
    def _check_schedule_overlap(self):
        """Перевірка на перетин робочих годин"""
        for record in self:
            # Перевірка для регулярного розкладу (day_of_week)
            if record.day_of_week and not record.date:
                overlapping = self.search([
                    ('id', '!=', record.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('day_of_week', '=', record.day_of_week),
                    ('date', '=', False),
                    ('active', '=', True),
                    '|',
                    '&',
                    ('time_from', '<=', record.time_from),
                    ('time_to', '>', record.time_from),
                    '&',
                    ('time_from', '<', record.time_to),
                    ('time_to', '>=', record.time_to),
                ], limit=1)
                if overlapping:
                    raise ValidationError(
                        _('Schedule overlaps with existing work hours!')
                    )
            # Перевірка для конкретної дати
            elif record.date:
                overlapping = self.search([
                    ('id', '!=', record.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('date', '=', record.date),
                    ('active', '=', True),
                    '|',
                    '&',
                    ('time_from', '<=', record.time_from),
                    ('time_to', '>', record.time_from),
                    '&',
                    ('time_from', '<', record.time_to),
                    ('time_to', '>=', record.time_to),
                ], limit=1)
                if overlapping:
                    raise ValidationError(
                        _('Schedule overlaps with existing hours '
                          'on this date!')
                    )
