from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrHospitalDiagnosis(models.Model):
    """Patient Diagnosis model.

    Represents medical diagnoses made during patient visits. Supports
    approval workflow where intern diagnoses require mentor approval.
    Automatically computes disease type from hierarchical disease structure.

    Features:
        - Multiple diagnoses per visit
        - Severity levels (mild, moderate, severe, critical)
        - Approval workflow with tracking
        - Disease type computation from hierarchy
    """
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
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        related='visit_id.patient_id',
        store=True,
        index=True,
        readonly=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        related='visit_id.doctor_id',
        store=True,
        index=True,
        readonly=True,
    )
    visit_date = fields.Datetime(
        related='visit_id.scheduled_date',
        store=True,
        index=True,
        readonly=True,
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease',
        required=True,
        domain="[('is_contagious', '=', True), "
               "('danger_level', 'in', ['high', 'critical'])]",
        help='Diagnosed disease',
    )
    disease_type_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease Type',
        compute='_compute_disease_type_id',
        store=True,
        index=True,
        readonly=True,
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
        comodel_name='res.partner',
        string='Approved By',
        readonly=True,
        help='Partner (doctor) who approved this diagnosis',
    )
    approval_date = fields.Datetime(
        readonly=True,
        help='Date and time when diagnosis was approved',
    )
    approved_date = fields.Datetime(
        readonly=True,
        help='Date and time when diagnosis was approved (alias for tests/backward compatibility)',
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

    @api.depends('disease_id', 'disease_id.parent_id')
    def _compute_disease_type_id(self):
        for record in self:
            record.disease_type_id = (
                record.disease_id.parent_id or record.disease_id
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

            record.write({
                'is_approved': True,
                'approved_by_id': doctor.partner_id.id
                if doctor else self.env.user.partner_id.id,
                'approval_date': fields.Datetime.now(),
                'approved_date': fields.Datetime.now(),
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
                'approved_date': False,
            })
