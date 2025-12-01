from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrHospitalDiagnosis(models.Model):
    """Діагноз пацієнта під час візиту"""
    _name = 'hr.hospital.diagnosis'
    _description = 'Patient Diagnosis'
    _order = 'visit_id, sequence, id'

    # Базові поля
    visit_id = fields.Many2one(
        comodel_name='hr.hospital.visit',
        string='Visit',
        required=True,
        ondelete='cascade',
        index=True,
        domain="[('status', '=', 'completed')]",
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease',
        required=True,
        domain="[('is_contagious', '=', True), "
               "('danger_level', 'in', ['high', 'critical'])]",
        help='Diagnosed disease',
    )
    diagnosis_type = fields.Selection(
        selection=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('complication', 'Complication'),
        ],
        default='primary',
        required=True,
    )
    sequence = fields.Integer(
        default=10,
        help='Sequence order for display',
    )

    # Опис та лікування
    description = fields.Text(
        string='Diagnosis Description',
        help='Additional details about the diagnosis',
        translate=True,
    )
    treatment = fields.Html(
        string='Prescribed Treatment',
        help='Detailed treatment plan',
        translate=True,
    )

    # Затвердження
    is_approved = fields.Boolean(
        string='Approved',
        default=False,
        help='Diagnosis has been approved by a doctor',
    )
    approved_by_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Approved By',
        readonly=True,
        help='Doctor who approved this diagnosis',
    )
    approval_date = fields.Datetime(
        readonly=True,
        help='Date and time when diagnosis was approved',
    )

    # Ступінь тяжкості
    severity = fields.Selection(
        selection=[
            ('mild', 'Mild'),
            ('moderate', 'Moderate'),
            ('severe', 'Severe'),
            ('critical', 'Critical'),
        ],
        help='Severity level of the diagnosis',
    )

    active = fields.Boolean(
        default=True,
    )

    @api.constrains('approval_date', 'visit_id')
    def _check_approval_date(self):
        """Валідація дати затвердження діагнозу"""
        for record in self:
            if record.approval_date and record.visit_id:
                visit_date = record.visit_id.scheduled_date
                if visit_date and record.approval_date < visit_date:
                    raise ValidationError(
                        _('Approval date cannot be earlier than visit date!')
                    )

    def action_approve(self):
        """Затверджує діагноз поточним лікарем"""
        for record in self:
            if record.is_approved:
                raise UserError(
                    _('This diagnosis is already approved!')
                )

            # Знаходимо лікаря пов'язаного з поточним користувачем
            doctor = self.env['hr.hospital.doctor'].search([
                ('user_id', '=', self.env.user.id)
            ], limit=1)

            if not doctor:
                raise UserError(
                    _('Current user is not linked to any doctor!')
                )

            record.write({
                'is_approved': True,
                'approved_by_id': doctor.id,
                'approval_date': fields.Datetime.now(),
            })

    def action_unapprove(self):
        """Скасовує затвердження діагнозу"""
        for record in self:
            if not record.is_approved:
                raise UserError(
                    _('This diagnosis is not approved!')
                )

            record.write({
                'is_approved': False,
                'approved_by_id': False,
                'approval_date': False,
            })
