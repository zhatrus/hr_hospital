from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DiseaseReportWizard(models.TransientModel):
    """Візард звіту по хворобах за період"""
    _name = 'disease.report.wizard'
    _description = 'Disease Report Wizard'

    @api.model
    def _default_date_from(self):
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    # Фільтри
    doctor_ids = fields.Many2many(
        comodel_name='hr.hospital.doctor',
        string='Doctors',
        help='Filter by doctors (empty = all doctors)',
    )
    disease_ids = fields.Many2many(
        comodel_name='hr.hospital.disease',
        string='Diseases',
        help='Filter by diseases (empty = all diseases)',
    )

    # Період
    date_from = fields.Date(
        required=True,
        default=_default_date_from,
        help='Start date of report period',
    )
    date_to = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='End date of report period',
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Валідація дат"""
        for record in self:
            if record.date_from > record.date_to:
                raise UserError(
                    _('Date From must be earlier than Date To!')
                )

    def action_generate_report(self):
        """Генерує звіт по хворобах"""
        self.ensure_one()

        domain = self._build_domain()
        context = dict(self.env.context, group_by=['disease_id'])

        return {
            'type': 'ir.actions.act_window',
            'name': _('Disease Report: %(from)s - %(to)s') % {
                'from': self.date_from,
                'to': self.date_to,
            },
            'res_model': 'hr.hospital.diagnosis',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': context,
        }

    def _build_domain(self):
        """Будує domain для пошуку діагнозів"""
        domain = []

        # Фільтр по даті візиту
        date_from_dt = datetime.combine(self.date_from, datetime.min.time())
        date_to_dt = datetime.combine(
            self.date_to + timedelta(days=1),
            datetime.min.time(),
        )
        date_from_str = fields.Datetime.to_string(date_from_dt)
        date_to_str = fields.Datetime.to_string(date_to_dt)
        domain.append(
            ('visit_date', '>=', date_from_str)
        )
        domain.append(
            ('visit_date', '<', date_to_str)
        )

        # Фільтр по лікарям
        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        # Фільтр по хворобам
        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))

        return domain
