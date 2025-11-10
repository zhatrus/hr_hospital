from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalPatient(models.Model):
    _name = 'hr.hospital.patient'
    _description = 'Hospital Patient'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'

    # Успадковані поля з abstract.person:
    # - last_name, first_name, middle_name
    # - phone, email
    # - gender, date_of_birth
    # - age (computed), full_name (computed)
    # - country_id, lang_id
    # - image fields (з image.mixin)

    # Базові поля
    address = fields.Text(
    )

    # Лікарі
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Personal Doctor',
        help='Current personal doctor of the patient',
        tracking=True,
    )

    # Паспортні дані
    passport_data = fields.Char(
        size=10,
        help='Passport number or ID',
    )

    # Контактна особа (основна)
    primary_contact_id = fields.Many2one(
        comodel_name='hr.hospital.contact.person',
        string='Primary Contact Person',
        domain="[('patient_id', '=', id)]",
        help='Main emergency contact person',
    )

    # Медична інформація
    blood_type = fields.Selection(
        selection=[
            ('o_positive', 'O(I) Rh+'),
            ('o_negative', 'O(I) Rh-'),
            ('a_positive', 'A(II) Rh+'),
            ('a_negative', 'A(II) Rh-'),
            ('b_positive', 'B(III) Rh+'),
            ('b_negative', 'B(III) Rh-'),
            ('ab_positive', 'AB(IV) Rh+'),
            ('ab_negative', 'AB(IV) Rh-'),
        ],
        help='Blood type with Rh factor',
    )
    allergies = fields.Text(
        help='List of known allergies',
    )

    # Страхування
    insurance_company_id = fields.Many2one(
        comodel_name='res.partner',
        string='Insurance Company',
        domain="[('is_company', '=', True)]",
        help='Insurance provider company',
    )
    insurance_policy_number = fields.Char(
        help='Policy or contract number',
    )

    # Відносини
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='patient_id',
        string='Visits',
    )
    contact_person_ids = fields.One2many(
        comodel_name='hr.hospital.contact.person',
        inverse_name='patient_id',
        string='Contact Persons',
    )
    doctor_history_ids = fields.One2many(
        comodel_name='hr.hospital.patient.doctor.history',
        inverse_name='patient_id',
        string='Doctor Assignment History',
    )

    @api.constrains('passport_data')
    def _check_passport_data(self):
        """Валідація паспортних даних"""
        for record in self:
            if record.passport_data:
                if len(record.passport_data) > 10:
                    raise ValidationError(
                        _('Passport data cannot exceed 10 characters!')
                    )

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        """Валідація віку пацієнта"""
        for record in self:
            if record.date_of_birth:
                if record.date_of_birth > fields.Date.today():
                    raise ValidationError(
                        _('Date of birth cannot be in the future!')
                    )
                # Перевіряємо що вік більше 0 (народився мінімум вчора)
                if record.date_of_birth == fields.Date.today():
                    raise ValidationError(
                        _('Patient age must be greater than 0!')
                    )

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        """При зміні лікаря, попереджуємо про необхідність
        оновлення історії"""
        if self.doctor_id and self.id:
            return {
                'warning': {
                    'title': _('Doctor Changed'),
                    'message': _(
                        'Personal doctor has been changed. '
                        'History record will be created automatically.'
                    ),
                }
            }
        return {}

    def write(self, vals):
        """Автоматичне створення історії при зміні лікаря"""
        result = super().write(vals)
        if 'doctor_id' in vals:
            for record in self:
                # Закриваємо попереднє призначення
                current_assignment = self.env[
                    'hr.hospital.patient.doctor.history'
                ].search([
                    ('patient_id', '=', record.id),
                    ('is_active', '=', True),
                ], limit=1)
                if current_assignment:
                    current_assignment.write({
                        'change_date': fields.Date.today(),
                        'is_active': False,
                    })

                # Створюємо нове призначення якщо є лікар
                if vals['doctor_id']:
                    self.env['hr.hospital.patient.doctor.history'].create({
                        'patient_id': record.id,
                        'doctor_id': vals['doctor_id'],
                        'assignment_date': fields.Date.today(),
                        'is_active': True,
                    })
        return result
