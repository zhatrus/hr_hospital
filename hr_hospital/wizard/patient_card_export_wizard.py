import base64
import csv
import json
from io import StringIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PatientCardExportWizard(models.TransientModel):
    """Візард експорту медичної картки пацієнта"""
    _name = 'patient.card.export.wizard'
    _description = 'Patient Card Export Wizard'

    # Основні параметри
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True,
        help='Patient to export medical card for',
    )
    date_from = fields.Date(
        help='Start date for filtering visits (empty = all)',
    )
    date_to = fields.Date(
        help='End date for filtering visits (empty = all)',
    )

    # Опції експорту
    include_diagnoses = fields.Boolean(
        default=True,
        help='Include diagnoses in export',
    )
    include_recommendations = fields.Boolean(
        default=True,
        help='Include visit recommendations in export',
    )
    report_lang = fields.Many2one(
        comodel_name='res.lang',
        string='Report Language',
        help='Language for report (default = patient language)',
    )
    export_format = fields.Selection(
        selection=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        required=True,
        default='json',
        help='Export file format',
    )

    # Результат експорту
    export_file = fields.Binary(
        string='Exported File',
        readonly=True,
        help='Exported medical card file',
    )
    export_filename = fields.Char(
        string='Filename',
        readonly=True,
        help='Name of exported file',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'patient_id' not in fields_list:
            return res

        if res.get('patient_id'):
            return res

        if self.env.context.get('active_model') != 'hr.hospital.patient':
            return res

        active_id = self.env.context.get('active_id')
        if not active_id:
            active_ids = self.env.context.get('active_ids') or []
            active_id = active_ids[0] if active_ids else False

        if active_id:
            res['patient_id'] = active_id
        return res

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """Встановлює мову звіту по замовчуванню"""
        if self.patient_id:
            # Спробувати взяти мову з країни пацієнта
            if self.patient_id.country_id:
                lang = self.env['res.lang'].search([
                    ('code', '=', self.patient_id.country_id.code.lower())
                ], limit=1)
                if lang:
                    self.report_lang = lang
            # Якщо не знайдено - мова користувача
            if not self.report_lang:
                self.report_lang = self.env['res.lang'].search([
                    ('code', '=', self.env.user.lang)
                ], limit=1)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Валідація дат"""
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError(
                        _('Date From must be earlier than Date To!')
                    )

    def action_export(self):
        """Експортує медичну картку пацієнта"""
        self.ensure_one()

        # Збираємо дані
        card_data = self._collect_patient_data()

        # Генеруємо файл в залежності від формату
        if self.export_format == 'json':
            file_content, filename = self._generate_json(card_data)
        else:
            file_content, filename = self._generate_csv(card_data)

        # Зберігаємо файл
        self.write({
            'export_file': base64.b64encode(file_content.encode('utf-8')),
            'export_filename': filename,
        })

        # Повертаємо action для завантаження
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'patient.card.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def _collect_patient_data(self):
        """Збирає дані пацієнта для експорту"""
        patient = self.patient_id

        # Базова інформація про пацієнта
        data = {
            'patient': {
                'name': patient.full_name,
                'date_of_birth': str(patient.date_of_birth) if
                patient.date_of_birth else None,
                'age': patient.age,
                'gender': patient.gender,
                'phone': patient.phone or '',
                'email': patient.email or '',
                'country': patient.country_id.name if
                patient.country_id else '',
                'doctor': patient.doctor_id.full_name if
                patient.doctor_id else '',
            },
            'visits': [],
        }

        # Фільтруємо візити по даті
        domain = [('patient_id', '=', patient.id)]
        if self.date_from:
            domain.append(('scheduled_date', '>=',
                          fields.Datetime.to_string(
                              fields.Datetime.from_string(self.date_from))))
        if self.date_to:
            domain.append(('scheduled_date', '<=',
                          fields.Datetime.to_string(
                              fields.Datetime.from_string(
                                  self.date_to).replace(
                                      hour=23, minute=59, second=59))))

        visits = self.env['hr.hospital.visit'].search(
            domain, order='scheduled_date desc'
        )

        # Збираємо інформацію про візити
        for visit in visits:
            visit_data = {
                'date': str(visit.scheduled_date) if
                visit.scheduled_date else '',
                'doctor': visit.doctor_id.full_name,
                'status': visit.status,
                'visit_type': visit.visit_type,
            }

            if self.include_recommendations and visit.recommendations:
                visit_data['recommendations'] = visit.recommendations

            if self.include_diagnoses and visit.diagnosis_ids:
                visit_data['diagnoses'] = []
                for diagnosis in visit.diagnosis_ids:
                    diagnosis_data = {
                        'disease': diagnosis.disease_id.name,
                        'icd_code': diagnosis.disease_id.icd_code or '',
                        'severity': diagnosis.severity or '',
                        'is_approved': diagnosis.is_approved,
                    }
                    if diagnosis.notes:
                        diagnosis_data['notes'] = diagnosis.notes
                    visit_data['diagnoses'].append(diagnosis_data)

            data['visits'].append(visit_data)

        return data

    def _generate_json(self, data):
        """Генерує JSON файл"""
        filename = (
            f"patient_card_{self.patient_id.id}_"
            f"{fields.Date.today().strftime('%Y%m%d')}.json"
        )

        # Форматуємо JSON з відступами для читабельності
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        return json_content, filename

    def _generate_csv(self, data):
        """Генерує CSV файл"""
        filename = (
            f"patient_card_{self.patient_id.id}_"
            f"{fields.Date.today().strftime('%Y%m%d')}.csv"
        )

        output = StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Заголовок - інформація про пацієнта
        writer.writerow(['PATIENT MEDICAL CARD'])
        writer.writerow(['Name', data['patient']['name']])
        writer.writerow(['Date of Birth', data['patient']['date_of_birth']])
        writer.writerow(['Age', data['patient']['age']])
        writer.writerow(['Gender', data['patient']['gender']])
        writer.writerow(['Phone', data['patient']['phone']])
        writer.writerow(['Email', data['patient']['email']])
        writer.writerow(['Country', data['patient']['country']])
        writer.writerow(['Doctor', data['patient']['doctor']])
        writer.writerow([])

        # Таблиця візитів
        writer.writerow(['VISITS'])
        headers = ['Date', 'Doctor', 'Status', 'Type']
        if self.include_recommendations:
            headers.append('Recommendations')
        if self.include_diagnoses:
            headers.extend(['Diagnoses', 'ICD Code', 'Severity'])
        writer.writerow(headers)

        for visit in data['visits']:
            row = [
                visit['date'],
                visit['doctor'],
                visit['status'],
                visit['visit_type'],
            ]
            if self.include_recommendations:
                row.append(visit.get('recommendations', ''))

            if self.include_diagnoses and visit.get('diagnoses'):
                # Перший діагноз в тому ж рядку
                first_diag = visit['diagnoses'][0]
                row.extend([
                    first_diag['disease'],
                    first_diag['icd_code'],
                    first_diag['severity'],
                ])
                writer.writerow(row)

                # Інші діагнози в окремих рядках
                for diag in visit['diagnoses'][1:]:
                    diag_row = [''] * (len(headers) - 3)
                    diag_row.extend([
                        diag['disease'],
                        diag['icd_code'],
                        diag['severity'],
                    ])
                    writer.writerow(diag_row)
            else:
                if self.include_diagnoses:
                    row.extend(['', '', ''])
                writer.writerow(row)

        return output.getvalue(), filename

    def action_download(self):
        """Завантажує експортований файл"""
        self.ensure_one()

        if not self.export_file:
            raise UserError(_('No file to download! Please export first.'))

        return {
            'type': 'ir.actions.act_url',
            'url': (
                f"/web/content/patient.card.export.wizard/{self.id}/"
                f"export_file/{self.export_filename}?download=true"
            ),
            'target': 'self',
        }
