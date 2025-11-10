from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDisease(models.Model):
    _name = 'hr.hospital.disease'
    _description = 'Hospital Disease'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'parent_path'

    name = fields.Char(
        string='Disease Name',
        required=True,
    )
    description = fields.Text(
        string='Description Disease',
    )

    # Ієрархічна структура
    parent_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Parent Disease',
        ondelete='restrict',
        index=True,
        help='Parent disease category',
    )
    parent_path = fields.Char(
        index=True,
        unaccent=False,
    )
    child_ids = fields.One2many(
        comodel_name='hr.hospital.disease',
        inverse_name='parent_id',
        string='Child Diseases',
        help='Sub-diseases or variations',
    )

    # Код МКХ-10
    icd_code = fields.Char(
        string='ICD-10 Code',
        size=10,
        help='International Classification of Diseases code',
    )

    # Характеристики
    danger_level = fields.Selection(
        selection=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        help='Level of danger this disease poses',
    )
    is_contagious = fields.Boolean(
        string='Contagious',
        default=False,
        help='Whether the disease is contagious',
    )
    symptoms = fields.Text(
        help='Common symptoms of the disease',
    )

    # Географія
    region_ids = fields.Many2many(
        comodel_name='res.country',
        relation='hr_hospital_disease_country_rel',
        column1='disease_id',
        column2='country_id',
        string='Regions',
        help='Countries/regions where disease is prevalent',
    )

    # Backward compatibility
    code = fields.Char(
        compute='_compute_code',
        inverse='_inverse_code',
        store=True,
        string='Disease Code',
        help='Alias for ICD-10 code (for backward compatibility)',
    )

    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='disease_id',
        string='Visits',
    )

    @api.depends('icd_code')
    def _compute_code(self):
        """Для зворотної сумісності"""
        for record in self:
            record.code = record.icd_code

    def _inverse_code(self):
        """Для зворотної сумісності"""
        for record in self:
            record.icd_code = record.code

    @api.constrains('icd_code')
    def _check_icd_code(self):
        """Валідація коду МКХ-10"""
        for record in self:
            if record.icd_code and len(record.icd_code) > 10:
                raise ValidationError(
                    _('ICD-10 code cannot exceed 10 characters!')
                )

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Перевірка на рекурсивну ієрархію"""
        if not self._check_recursion():
            raise ValidationError(
                _('You cannot create recursive disease hierarchy!')
            )
