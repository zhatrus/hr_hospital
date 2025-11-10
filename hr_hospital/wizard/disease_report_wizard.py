from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DiseaseReportWizard(models.TransientModel):
    """Візард звіту по хворобах за період"""
    _name = 'disease.report.wizard'
    _description = 'Disease Report Wizard'

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
    country_ids = fields.Many2many(
        comodel_name='res.country',
        string='Countries',
        help='Filter by patient citizenship country',
    )

    # Період
    date_from = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='Start date of report period',
    )
    date_to = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='End date of report period',
    )

    # Налаштування звіту
    report_type = fields.Selection(
        selection=[
            ('detailed', 'Detailed'),
            ('summary', 'Summary'),
        ],
        required=True,
        default='detailed',
        help='Type of report to generate',
    )
    group_by = fields.Selection(
        selection=[
            ('doctor', 'By Doctor'),
            ('disease', 'By Disease'),
            ('month', 'By Month'),
            ('country', 'By Country'),
        ],
        help='Group results by selected field',
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

        # Будуємо domain для пошуку діагнозів
        domain = self._build_domain()

        # Отримуємо діагнози
        diagnoses = self.env['hr.hospital.diagnosis'].search(domain)

        if not diagnoses:
            raise UserError(
                _('No diagnoses found for selected criteria!')
            )

        # Генеруємо дані в залежності від типу звіту
        if self.report_type == 'detailed':
            data = self._generate_detailed_report(diagnoses)
        else:
            data = self._generate_summary_report(diagnoses)

        # Повертаємо результат
        return self._display_report(data)

    def _build_domain(self):
        """Будує domain для пошуку діагнозів"""
        domain = []

        # Фільтр по даті візиту
        domain.append(('visit_id.scheduled_date', '>=',
                      fields.Datetime.to_string(
                          fields.Datetime.from_string(self.date_from))))
        domain.append(('visit_id.scheduled_date', '<=',
                      fields.Datetime.to_string(
                          fields.Datetime.from_string(self.date_to) +
                          fields.Datetime.now().replace(
                              hour=23, minute=59, second=59) -
                          fields.Datetime.now().replace(
                              hour=0, minute=0, second=0))))

        # Фільтр по лікарям
        if self.doctor_ids:
            domain.append(('visit_id.doctor_id', 'in', self.doctor_ids.ids))

        # Фільтр по хворобам
        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))

        # Фільтр по країнам пацієнтів
        if self.country_ids:
            domain.append(
                ('visit_id.patient_id.country_id', 'in', self.country_ids.ids)
            )

        return domain

    def _generate_detailed_report(self, diagnoses):
        """Генерує детальний звіт"""
        data = {
            'report_type': 'detailed',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'total_diagnoses': len(diagnoses),
            'lines': [],
        }

        if self.group_by:
            data['lines'] = self._group_diagnoses(diagnoses, self.group_by)
        else:
            # Без групування - просто список
            for diagnosis in diagnoses:
                data['lines'].append({
                    'diagnosis_id': diagnosis.id,
                    'disease': diagnosis.disease_id.name,
                    'icd_code': diagnosis.disease_id.icd_code or '',
                    'patient': diagnosis.visit_id.patient_id.full_name,
                    'doctor': diagnosis.visit_id.doctor_id.full_name,
                    'date': diagnosis.visit_id.scheduled_date,
                    'severity': diagnosis.severity,
                    'is_approved': diagnosis.is_approved,
                })

        return data

    def _generate_summary_report(self, diagnoses):
        """Генерує підсумковий звіт"""
        data = {
            'report_type': 'summary',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'total_diagnoses': len(diagnoses),
            'statistics': {},
        }

        # Статистика по тяжкості
        severity_stats = {}
        for diagnosis in diagnoses:
            severity = diagnosis.severity or 'not_set'
            severity_stats[severity] = severity_stats.get(severity, 0) + 1

        data['statistics']['by_severity'] = severity_stats

        # Статистика по затвердженню
        approved = len(diagnoses.filtered(lambda d: d.is_approved))
        data['statistics']['approved'] = approved
        data['statistics']['not_approved'] = len(diagnoses) - approved

        # Топ-5 хвороб
        disease_counts = {}
        for diagnosis in diagnoses:
            disease_name = diagnosis.disease_id.name
            disease_counts[disease_name] = \
                disease_counts.get(disease_name, 0) + 1

        top_diseases = sorted(
            disease_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        data['statistics']['top_diseases'] = [
            {'disease': name, 'count': count}
            for name, count in top_diseases
        ]

        # Групування якщо вказано
        if self.group_by:
            data['grouped'] = self._group_diagnoses(diagnoses, self.group_by)

        return data

    def _group_diagnoses(self, diagnoses, group_by):
        """Групує діагнози за вказаним полем"""
        grouped = {}

        for diagnosis in diagnoses:
            if group_by == 'doctor':
                key = diagnosis.visit_id.doctor_id.full_name
            elif group_by == 'disease':
                key = diagnosis.disease_id.name
            elif group_by == 'month':
                date = diagnosis.visit_id.scheduled_date
                key = date.strftime('%Y-%m') if date else 'Unknown'
            elif group_by == 'country':
                country = diagnosis.visit_id.patient_id.country_id
                key = country.name if country else 'Unknown'
            else:
                key = 'Other'

            if key not in grouped:
                grouped[key] = []

            grouped[key].append({
                'diagnosis_id': diagnosis.id,
                'disease': diagnosis.disease_id.name,
                'patient': diagnosis.visit_id.patient_id.full_name,
                'doctor': diagnosis.visit_id.doctor_id.full_name,
                'date': diagnosis.visit_id.scheduled_date,
                'severity': diagnosis.severity,
            })

        # Перетворюємо в список для зручності
        result = []
        for key, items in grouped.items():
            result.append({
                'group_name': key,
                'count': len(items),
                'items': items,
            })

        # Сортуємо по кількості (більше спочатку)
        result.sort(key=lambda x: x['count'], reverse=True)

        return result

    def _display_report(self, data):
        """Відображає звіт"""
        # Для простого відображення повертаємо tree view
        # В реальному проекті тут можна згенерувати PDF/Excel

        # Зберігаємо дані в context для передачі у view
        context = self.env.context.copy()
        context.update({
            'report_data': data,
            'wizard_id': self.id,
        })

        # Повертаємо action для відображення результату
        return {
            'type': 'ir.actions.act_window',
            'name': _('Disease Report: %(from)s - %(to)s') % {
                'from': self.date_from,
                'to': self.date_to,
            },
            'res_model': 'hr.hospital.diagnosis',
            'view_mode': 'tree,form',
            'domain': self._build_domain(),
            'context': context,
        }
