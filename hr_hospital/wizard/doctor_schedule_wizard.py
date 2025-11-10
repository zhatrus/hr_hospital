from datetime import timedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DoctorScheduleWizard(models.TransientModel):
    """Візард для заповнення розкладу лікаря"""
    _name = 'doctor.schedule.wizard'
    _description = 'Doctor Schedule Wizard'

    # Основні параметри
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
        help='Doctor for schedule generation',
    )
    week_start = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='Start date of first week',
    )
    weeks_count = fields.Integer(
        string='Number of Weeks',
        required=True,
        default=1,
        help='Number of weeks to generate schedule for',
    )
    schedule_type = fields.Selection(
        selection=[
            ('standard', 'Standard'),
            ('even_week', 'Even Week'),
            ('odd_week', 'Odd Week'),
        ],
        required=True,
        default='standard',
        help='Type of schedule',
    )

    # Дні тижня
    monday = fields.Boolean(
        default=True,
        help='Generate schedule for Monday',
    )
    tuesday = fields.Boolean(
        default=True,
        help='Generate schedule for Tuesday',
    )
    wednesday = fields.Boolean(
        default=True,
        help='Generate schedule for Wednesday',
    )
    thursday = fields.Boolean(
        default=True,
        help='Generate schedule for Thursday',
    )
    friday = fields.Boolean(
        default=True,
        help='Generate schedule for Friday',
    )
    saturday = fields.Boolean(
        default=False,
        help='Generate schedule for Saturday',
    )
    sunday = fields.Boolean(
        default=False,
        help='Generate schedule for Sunday',
    )

    # Робочий час
    time_from = fields.Float(
        required=True,
        default=9.0,
        help='Work start time (e.g., 9.0 for 09:00)',
    )
    time_to = fields.Float(
        required=True,
        default=18.0,
        help='Work end time (e.g., 18.0 for 18:00)',
    )

    # Перерва
    break_from = fields.Float(
        help='Break start time (optional)',
    )
    break_to = fields.Float(
        help='Break end time (optional)',
    )

    @api.constrains('weeks_count')
    def _check_weeks_count(self):
        """Валідація кількості тижнів"""
        for record in self:
            if record.weeks_count < 1:
                raise ValidationError(
                    _('Number of weeks must be at least 1!')
                )
            if record.weeks_count > 52:
                raise ValidationError(
                    _('Number of weeks cannot exceed 52!')
                )

    @api.constrains('time_from', 'time_to')
    def _check_work_time(self):
        """Валідація робочого часу"""
        for record in self:
            if record.time_from < 0 or record.time_from >= 24:
                raise ValidationError(
                    _('Work start time must be between 0.00 and 23.59!')
                )
            if record.time_to < 0 or record.time_to >= 24:
                raise ValidationError(
                    _('Work end time must be between 0.00 and 23.59!')
                )
            if record.time_from >= record.time_to:
                raise ValidationError(
                    _('Work end time must be later than work start time!')
                )

    @api.constrains('break_from', 'break_to', 'time_from', 'time_to')
    def _check_break_time(self):
        """Валідація часу перерви"""
        for record in self:
            if record.break_from or record.break_to:
                if not (record.break_from and record.break_to):
                    raise ValidationError(
                        _('Both break start and break end must be set!')
                    )
                if record.break_from >= record.break_to:
                    raise ValidationError(
                        _('Break end must be later than break start!')
                    )
                if (record.break_from < record.time_from or
                        record.break_to > record.time_to):
                    raise ValidationError(
                        _('Break must be within work hours!')
                    )

    def action_generate_schedule(self):
        """Генерує розклад для лікаря"""
        self.ensure_one()

        # Перевірка що вибрано хоча б один день
        if not any([
            self.monday, self.tuesday, self.wednesday,
            self.thursday, self.friday, self.saturday, self.sunday
        ]):
            raise UserError(
                _('Please select at least one day of the week!')
            )

        # Мапінг днів тижня
        weekdays = {
            0: self.monday,
            1: self.tuesday,
            2: self.wednesday,
            3: self.thursday,
            4: self.friday,
            5: self.saturday,
            6: self.sunday,
        }

        created_count = 0
        skipped_count = 0

        # Початок тижня - понеділок
        start_date = self.week_start
        # Знаходимо найближчий понеділок
        days_to_monday = start_date.weekday()
        week_monday = start_date - timedelta(days=days_to_monday)

        # Генеруємо розклад для кожного тижня
        for week_num in range(self.weeks_count):
            current_week_start = week_monday + timedelta(weeks=week_num)

            # Визначаємо чи генерувати для цього тижня
            # (для парних/непарних тижнів)
            week_number = current_week_start.isocalendar()[1]
            if self.schedule_type == 'even_week' and week_number % 2 != 0:
                continue
            if self.schedule_type == 'odd_week' and week_number % 2 == 0:
                continue

            # Генеруємо для кожного дня тижня
            for day_num in range(7):
                if not weekdays[day_num]:
                    continue

                current_date = current_week_start + timedelta(days=day_num)

                # Перевірка чи не існує вже розклад
                existing = self.env['hr.hospital.doctor.schedule'].search([
                    ('doctor_id', '=', self.doctor_id.id),
                    ('date', '=', current_date),
                ], limit=1)

                if existing:
                    skipped_count += 1
                    continue

                # Створюємо розклад
                schedule_data = {
                    'doctor_id': self.doctor_id.id,
                    'date': current_date,
                    'time_from': self.time_from,
                    'time_to': self.time_to,
                    'schedule_type': self.schedule_type,
                }

                # Додаємо перерву якщо вказана
                if self.break_from and self.break_to:
                    schedule_data.update({
                        'notes': _(
                            'Break: %(from)s - %(to)s'
                        ) % {
                            'from': self._format_time(self.break_from),
                            'to': self._format_time(self.break_to),
                        }
                    })

                self.env['hr.hospital.doctor.schedule'].create(schedule_data)
                created_count += 1

        # Повідомлення про результат
        message_parts = []
        if created_count:
            message_parts.append(
                _('Created %(count)d schedule entries') % {
                    'count': created_count
                }
            )
        if skipped_count:
            message_parts.append(
                _('Skipped %(count)d existing entries') % {
                    'count': skipped_count
                }
            )

        if not created_count and not skipped_count:
            raise UserError(_('No schedule entries were created!'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': '\n'.join(message_parts),
                'type': 'success',
                'sticky': False,
            }
        }

    def _format_time(self, time_float):
        """Форматує час з float в рядок"""
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return '%02d:%02d' % (hours, minutes)
