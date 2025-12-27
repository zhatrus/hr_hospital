import re
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AbstractPerson(models.AbstractModel):
    """Абстрактна модель "Особа" для зберігання спільних даних про людей"""
    _name = 'abstract.person'
    _description = 'Abstract Person Model'
    _inherit = ['image.mixin']

    # ПІБ (окремі поля)
    last_name = fields.Char(
        required=True,
        index=True,
    )
    first_name = fields.Char(
        required=True,
        index=True,
    )
    middle_name = fields.Char(
    )

    # Контактна інформація
    phone = fields.Char(
        help='Phone number in international format',
    )
    email = fields.Char(
    )

    # Особиста інформація
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
    )
    date_of_birth = fields.Date(
    )
    birth_date = fields.Date(
        string='Birth Date',
        related='date_of_birth',
        store=True,
        readonly=False,
        help='Alias for date of birth to support legacy usage',
    )

    # Обчислювальні поля
    age = fields.Integer(
        compute='_compute_age',
        store=True,
        help='Age calculated from date of birth',
    )
    full_name = fields.Char(
        compute='_compute_full_name',
        store=True,
        index=True,
    )

    # Додаткова інформація
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country of Citizenship',
    )
    lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Preferred Language',
    )

    @api.depends('date_of_birth')
    def _compute_age(self):
        """Обчислення віку від дати народження (точно по роках)"""
        for record in self:
            if record.date_of_birth:
                days = (date.today() - record.date_of_birth).days
                record.age = max(0, days // 365)
            else:
                record.age = 0

    @api.depends('last_name', 'first_name', 'middle_name')
    def _compute_full_name(self):
        """Обчислення повного імені"""
        for record in self:
            name_parts = []
            if record.last_name:
                name_parts.append(record.last_name)
            if record.first_name:
                name_parts.append(record.first_name)
            if record.middle_name:
                name_parts.append(record.middle_name)
            record.full_name = ' '.join(name_parts)

    @api.constrains('phone')
    def _check_phone(self):
        """Валідація українських мобільних номерів"""
        for record in self:
            if record.phone:
                # Видаляємо всі пробіли, дефіси та дужки для перевірки
                phone_clean = re.sub(r'[\s\-\(\)]', '', record.phone)

                # Дозволені коди українських мобільних операторів (2 цифри)
                mobile_codes = (
                    r'(39|50|63|66|67|68|73|75|77|89|'
                    r'91|92|93|94|95|96|97|98|99)'
                )

                # Формати: +380XXXXXXXXX або 0XXXXXXXXX (2 цифри код + 7 цифр)
                phone_pattern = (
                    rf'^(\+380{mobile_codes}|0{mobile_codes})\d{{7}}$'
                )

                if not re.match(phone_pattern, phone_clean):
                    raise ValidationError(
                        _('Phone number format is invalid. '
                          'Please use Ukrainian mobile number format: '
                          '+380XX XXX XX XX or 0XX XXX XX XX. '
                          'Allowed codes: 39, 50, 63, 66, 67, '
                          '68, 73, 75, 77, 89, 91, 92, 93, 94, '
                          '95, 96, 97, 98, 99')
                    )

    @api.constrains('email')
    def _check_email(self):
        """Валідація формату email"""
        for record in self:
            if record.email:
                email_pattern = (
                    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                )
                if not re.match(email_pattern, record.email):
                    raise ValidationError(
                        _('Email format is invalid. '
                          'Please use format like example@domain.com')
                    )

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        """Валідація дати народження"""
        for record in self:
            if record.date_of_birth:
                if record.date_of_birth > date.today():
                    raise ValidationError(
                        _('Date of birth cannot be in the future!')
                    )
                # Перевірка мінімального віку (наприклад, не менше 0 років)
                age = (date.today() - record.date_of_birth).days / 365.25
                if age > 150:
                    raise ValidationError(
                        _('Age cannot be more than 150 years!')
                    )
