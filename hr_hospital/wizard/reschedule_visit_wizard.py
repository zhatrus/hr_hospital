from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RescheduleVisitWizard(models.TransientModel):
    """Візард для перенесення візиту"""
    _name = 'reschedule.visit.wizard'
    _description = 'Reschedule Visit Wizard'

    # Поточний візит
    visit_id = fields.Many2one(
        comodel_name='hr.hospital.visit',
        string='Current Visit',
        required=True,
        readonly=True,
        help='Visit to reschedule',
    )

    # Інформація про поточний візит (для відображення)
    current_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Current Doctor',
        related='visit_id.doctor_id',
        readonly=True,
    )
    current_patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        related='visit_id.patient_id',
        readonly=True,
    )
    current_scheduled_date = fields.Datetime(
        string='Current Date & Time',
        related='visit_id.scheduled_date',
        readonly=True,
    )

    # Нові дані
    new_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='New Doctor',
        help='New doctor (leave empty to keep current)',
    )
    new_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='New visit date',
    )
    new_time = fields.Float(
        required=True,
        help='New visit time (e.g., 14.5 for 14:30)',
    )
    reschedule_reason = fields.Text(
        string='Reason for Rescheduling',
        required=True,
        help='Reason why visit is being rescheduled',
    )

    @api.model
    def default_get(self, fields_list):
        """Встановлює значення за замовчуванням"""
        res = super().default_get(fields_list)

        # Отримуємо візит з контексту
        active_id = self.env.context.get('active_id')
        if active_id:
            visit = self.env['hr.hospital.visit'].browse(active_id)
            res['visit_id'] = active_id

            # Заповнюємо поточний час як базу для нового
            if visit.scheduled_date:
                current_time = visit.scheduled_date.hour + \
                    visit.scheduled_date.minute / 60.0
                res['new_time'] = current_time
                res['new_date'] = visit.scheduled_date.date()

        return res

    @api.constrains('new_time')
    def _check_new_time(self):
        """Валідація часу"""
        for record in self:
            if record.new_time < 0 or record.new_time >= 24:
                raise ValidationError(
                    _('Time must be between 0.00 and 23.59!')
                )

    @api.constrains('new_date')
    def _check_new_date(self):
        """Валідація дати"""
        for record in self:
            if record.new_date < fields.Date.today():
                raise ValidationError(
                    _('Cannot reschedule to a past date!')
                )

    def action_reschedule(self):
        """Виконує перенесення візиту"""
        self.ensure_one()

        # Перевірка що візит можна переносити
        if self.visit_id.status == 'completed':
            raise UserError(
                _('Cannot reschedule a completed visit!')
            )
        if self.visit_id.status == 'cancelled':
            raise UserError(
                _('Cannot reschedule a cancelled visit!')
            )

        # Визначаємо нового лікаря (або залишаємо поточного)
        new_doctor = self.new_doctor_id or self.visit_id.doctor_id

        # Формуємо нову дату+час
        new_datetime = fields.Datetime.to_datetime(self.new_date)
        hours = int(self.new_time)
        minutes = int((self.new_time - hours) * 60)
        new_datetime = new_datetime.replace(hour=hours, minute=minutes)

        # Перевірка чи не зайнятий цей слот
        existing_visit = self.env['hr.hospital.visit'].search([
            ('id', '!=', self.visit_id.id),
            ('doctor_id', '=', new_doctor.id),
            ('patient_id', '=', self.visit_id.patient_id.id),
            ('scheduled_date', '>=', new_datetime),
            ('scheduled_date', '<', new_datetime.replace(hour=23, minute=59)),
            ('status', 'not in', ['cancelled']),
        ], limit=1)

        if existing_visit:
            raise UserError(
                _('Patient already has a visit with this doctor '
                  'on selected date!')
            )

        # Зберігаємо стару інформацію для нотатки
        old_info = _(
            'Original: %(doctor)s on %(date)s\n'
            'Reason: %(reason)s'
        ) % {
            'doctor': self.visit_id.doctor_id.full_name,
            'date': self.visit_id.scheduled_date,
            'reason': self.reschedule_reason,
        }

        # Оновлюємо візит
        self.visit_id.write({
            'doctor_id': new_doctor.id,
            'scheduled_date': new_datetime,
            'recommendations': (
                (self.visit_id.recommendations or '') +
                '\n\n--- RESCHEDULED ---\n' + old_info
            ),
        })

        # Повідомлення про успіх
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _(
                    'Visit rescheduled to %(date)s at %(time)s '
                    'with doctor %(doctor)s'
                ) % {
                    'date': self.new_date,
                    'time': f"{hours:02d}:{minutes:02d}",
                    'doctor': new_doctor.full_name,
                },
                'type': 'success',
                'sticky': False,
            }
        }
