from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrHospitalDoctor(models.Model):
    _name = 'hr.hospital.doctor'
    _description = 'Hospital Doctor'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'

    # Успадковані поля з abstract.person:
    # - last_name, first_name, middle_name
    # - phone, email
    # - gender, date_of_birth
    # - age (computed), full_name (computed)
    # - country_id, lang_id
    # - image fields (з image.mixin)

    # Користувач системи
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='System User',
        help='User account for system login',
        ondelete='restrict',
    )

    # Спеціальність
    specialization_id = fields.Many2one(
        comodel_name='hr.hospital.doctor.specialization',
        string='Specialization',
        help='Medical specialization',
    )

    # Інтерн та ментор
    is_intern = fields.Boolean(
        default=False,
    )
    mentor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Mentor',
        domain="[('is_intern', '=', False)]",
        help='Mentor doctor (available only for interns)',
    )

    # Ліцензія
    license_number = fields.Char(
        required=True,
        copy=False,
        help='Medical license number',
    )
    license_issue_date = fields.Date(
        help='Date when medical license was issued',
    )
    years_of_experience = fields.Integer(
        string='Years of Experience',
        compute='_compute_years_of_experience',
        store=True,
        help='Years of experience based on license issue date',
    )

    # Рейтинг
    rating = fields.Float(
        digits=(3, 2),
        help='Doctor rating from 0.00 to 5.00',
    )

    # Країна навчання
    education_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Education Country',
        help='Country where doctor received education',
    )

    # Відносини
    intern_ids = fields.One2many(
        comodel_name='hr.hospital.doctor',
        inverse_name='mentor_id',
        string='Interns',
    )
    patient_ids = fields.One2many(
        comodel_name='hr.hospital.patient',
        inverse_name='doctor_id',
        string='Patients',
    )
    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='doctor_id',
        string='Visits',
    )
    schedule_ids = fields.One2many(
        comodel_name='hr.hospital.doctor.schedule',
        inverse_name='doctor_id',
        string='Work Schedule',
    )

    @api.depends('license_issue_date')
    def _compute_years_of_experience(self):
        """Обчислює досвід роботи від дати видачі ліцензії"""
        for record in self:
            if record.license_issue_date:
                today = fields.Date.today()
                delta = relativedelta(today, record.license_issue_date)
                record.years_of_experience = delta.years
            else:
                record.years_of_experience = 0

    @api.constrains('rating')
    def _check_rating(self):
        """Валідація рейтингу (0.00 - 5.00)"""
        for record in self:
            if record.rating:
                if record.rating < 0.00 or record.rating > 5.00:
                    raise ValidationError(
                        _('Rating must be between 0.00 and 5.00!')
                    )

    @api.constrains('license_issue_date')
    def _check_license_issue_date(self):
        """Валідація дати видачі ліцензії"""
        for record in self:
            if record.license_issue_date:
                if record.license_issue_date > fields.Date.today():
                    raise ValidationError(
                        _('License issue date cannot be in the future!')
                    )
