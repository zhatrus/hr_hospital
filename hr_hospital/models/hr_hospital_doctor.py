from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrHospitalDoctor(models.Model):
    """Hospital Doctor model.

    Represents medical doctors with their qualifications, specializations,
    and work schedules. Supports intern-mentor relationships and tracks
    years of experience based on license issue date.

    Inherits from abstract.person to get common personal data fields.
    """
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

    mentor_phone = fields.Char(
        related='mentor_id.phone',
        readonly=True,
    )
    mentor_email = fields.Char(
        related='mentor_id.email',
        readonly=True,
    )
    mentor_specialization_id = fields.Many2one(
        related='mentor_id.specialization_id',
        readonly=True,
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

    # Архівація
    active = fields.Boolean(
        default=True,
        help='Uncheck to archive the doctor',
    )

    # SQL Constraints
    _sql_constraints = [
        ('license_number_unique',
         'UNIQUE(license_number)',
         'License number must be unique!'),
        ('rating_check',
         'CHECK(rating >= 0.00 AND rating <= 5.00)',
         'Rating must be between 0.00 and 5.00!'),
    ]

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

    @api.constrains('license_issue_date')
    def _check_license_issue_date(self):
        """Валідація дати видачі ліцензії"""
        for record in self:
            if record.license_issue_date:
                if record.license_issue_date > fields.Date.today():
                    raise ValidationError(
                        _('License issue date cannot be in the future!')
                    )

    @api.constrains('mentor_id', 'is_intern')
    def _check_mentor(self):
        """Валідація вибору ментора"""
        for record in self:
            # Інтерн не може бути ментором
            if record.mentor_id and record.mentor_id.is_intern:
                raise ValidationError(
                    _('An intern cannot be a mentor!')
                )
            # Лікар не може бути ментором сам собі
            if record.mentor_id and record.mentor_id.id == record.id:
                raise ValidationError(
                    _('A doctor cannot be their own mentor!')
                )

    @api.constrains('active')
    def _check_archive_with_active_visits(self):
        """Заборона архівування лікарів з активними візитами"""
        for record in self:
            if not record.active:
                active_visits = self.env['hr.hospital.visit'].search([
                    ('doctor_id', '=', record.id),
                    ('scheduled_date', '>=', fields.Date.today()),
                ], limit=1)
                if active_visits:
                    raise ValidationError(
                        _('Cannot archive doctor with active visits! '
                          'Please reassign or cancel visits first.')
                    )

    def action_quick_create_visit(self):
        """Open Visit creation form with this doctor prefilled."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Visit'),
            'res_model': 'hr.hospital.visit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_doctor_id': self.id,
            },
        }
