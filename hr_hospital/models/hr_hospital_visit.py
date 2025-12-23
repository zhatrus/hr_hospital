from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrHospitalVisit(models.Model):
    _name = 'hr.hospital.visit'
    _description = 'Hospital Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    # Базові поля
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True,
        index=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
        index=True,
        domain="[('license_number', '!=', False)]",
    )

    # Статус візиту
    status = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ],
        string='Visit Status',
        default='scheduled',
        required=True,
        tracking=True,
    )

    # Дата та час
    scheduled_date = fields.Datetime(
        string='Scheduled Date & Time',
        required=True,
        default=fields.Datetime.now,
        index=True,
        help='Planned date and time of visit',
    )
    actual_date = fields.Datetime(
        string='Actual Date & Time',
        readonly=True,
        help='Actual date and time of visit (readonly if not completed)',
    )

    # Тип візиту
    visit_type = fields.Selection(
        selection=[
            ('primary', 'Primary'),
            ('followup', 'Follow-up'),
            ('preventive', 'Preventive'),
            ('emergency', 'Emergency'),
        ],
        required=True,
        default='primary',
    )

    # Старі поля (deprecated, але залишаємо для зворотної сумісності)
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease',
        help='Deprecated: use diagnosis_ids instead',
    )
    visit_date = fields.Datetime(
        string='Date Visit',
        compute='_compute_visit_date',
        store=True,
        help='Deprecated: use scheduled_date or actual_date',
    )
    notes = fields.Text(
        string='Notes Visit',
        translate=True,
    )
    diagnosis = fields.Text(
        string='Diagnosis Visit',
        help='Deprecated: use diagnosis_ids instead',
        translate=True,
    )
    prescription = fields.Text(
        string='Prescription Visit',
        translate=True,
    )

    # Нові поля
    diagnosis_ids = fields.One2many(
        comodel_name='hr.hospital.diagnosis',
        inverse_name='visit_id',
        string='Diagnoses',
    )
    recommendations = fields.Html(
        help='Medical recommendations for the patient',
        translate=True,
    )

    # Поля для динамічних доменів
    specialization_filter_id = fields.Many2one(
        comodel_name='hr.hospital.doctor.specialization',
        string='Filter by Specialization',
        help='Filter available doctors by specialization',
    )
    available_date_filter = fields.Date(
        string='Filter Available Date',
        help='Filter doctors with available schedule on this date',
    )

    # Вартість
    cost = fields.Monetary(
        string='Visit Cost',
        currency_field='currency_id',
        help='Cost of the visit',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends('actual_date', 'scheduled_date')
    def _compute_visit_date(self):
        """Обчислює visit_date для зворотної сумісності"""
        for record in self:
            record.visit_date = record.actual_date or record.scheduled_date

    @api.onchange('status')
    def _onchange_status(self):
        """При завершенні візиту встановлює actual_date"""
        if self.status == 'completed' and not self.actual_date:
            self.actual_date = fields.Datetime.now()
        elif self.status != 'completed':
            self.actual_date = False

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Валідація запланованої дати"""
        for record in self:
            if record.scheduled_date:
                # Дозволяємо тільки майбутні дати для нових візитів
                if not record.id and record.scheduled_date < \
                        fields.Datetime.now():
                    raise ValidationError(
                        _('Scheduled date cannot be in the past!')
                    )

    @api.constrains('actual_date', 'status')
    def _check_actual_date(self):
        """Валідація фактичної дати"""
        for record in self:
            if record.actual_date and record.status != 'completed':
                raise ValidationError(
                    _('Actual date can only be set for completed visits!')
                )
            if record.status == 'completed' and not record.actual_date:
                raise ValidationError(
                    _('Completed visit must have actual date!')
                )

    @api.constrains('patient_id', 'doctor_id', 'scheduled_date')
    def _check_duplicate_visit(self):
        """
        Заборона запису одного пацієнта до одного лікаря
        більше разу на день
        """
        for record in self:
            if (record.patient_id and record.doctor_id and
                    record.scheduled_date):
                # Отримуємо дату (без часу)
                visit_date = fields.Date.to_date(record.scheduled_date)

                # Шукаємо інші візити цього пацієнта до цього лікаря в цей день
                domain = [
                    ('id', '!=', record.id),
                    ('patient_id', '=', record.patient_id.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('scheduled_date', '>=', fields.Datetime.to_string(
                        fields.Datetime.from_string(visit_date))),
                    ('scheduled_date', '<', fields.Datetime.to_string(
                        fields.Datetime.from_string(visit_date) +
                        relativedelta(days=1))),
                    ('status', '!=', 'cancelled'),
                ]

                duplicate = self.search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        _('Patient %(patient)s already has a visit '
                          'scheduled with doctor %(doctor)s on %(date)s!') % {
                            'patient': record.patient_id.full_name,
                            'doctor': record.doctor_id.full_name,
                            'date': visit_date,
                        }
                    )

    def write(self, vals):
        """
        Заборона зміни лікаря/дати/часу для візитів
        що вже відбулись
        """
        for record in self:
            if record.status == 'completed':
                protected_fields = [
                    'doctor_id', 'scheduled_date', 'patient_id'
                ]
                if any(field in vals for field in protected_fields):
                    raise ValidationError(
                        _('Cannot change doctor, date or patient '
                          'for completed visits!')
                    )
        return super().write(vals)

    @api.onchange('specialization_filter_id', 'available_date_filter')
    def _onchange_doctor_filters(self):
        """Динамічний domain для doctor_id за спеціальністю та розкладом"""
        domain = [('license_number', '!=', False)]

        # Фільтр за спеціальністю
        if self.specialization_filter_id:
            domain.append(
                ('specialization_id', '=', self.specialization_filter_id.id)
            )

        # Фільтр за наявністю розкладу на дату
        if self.available_date_filter:
            doctors_with_schedule = self.env[
                'hr.hospital.doctor.schedule'
            ].search([
                ('date', '=', self.available_date_filter)
            ]).mapped('doctor_id')
            if doctors_with_schedule:
                domain.append(('id', 'in', doctors_with_schedule.ids))
            else:
                # Якщо немає розкладу - показуємо всіх
                pass

        return {'domain': {'doctor_id': domain}}

    def unlink(self):
        """Заборона видалення візитів з діагнозами"""
        for record in self:
            if record.diagnosis_ids:
                raise ValidationError(
                    _('Cannot delete visit with diagnoses! '
                      'Please remove diagnoses first.')
                )
        return super().unlink()

    def name_get(self):
        """Human-friendly display name for calendar/pickers."""
        result = []
        for record in self:
            patient_name = record.patient_id.full_name or record.patient_id.display_name
            doctor_name = record.doctor_id.full_name or record.doctor_id.display_name

            dt_str = False
            if record.scheduled_date:
                local_dt = fields.Datetime.context_timestamp(record, record.scheduled_date)
                dt_str = local_dt.strftime('%d.%m.%Y %H:%M')

            parts = [p for p in [patient_name, doctor_name, dt_str] if p]
            # pylint: disable=protected-access
            name = ' — '.join(parts) if parts else f"{record._name},{record.id}"
            result.append((record.id, name))
        return result
