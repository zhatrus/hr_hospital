from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MassReassignDoctorWizard(models.TransientModel):
    """Візард для масового перепризначення лікаря"""
    _name = 'mass.reassign.doctor.wizard'
    _description = 'Mass Reassign Doctor Wizard'

    old_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Old Doctor',
        help='Current doctor to be replaced',
    )
    new_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='New Doctor',
        required=True,
        help='New doctor to assign',
    )
    patient_ids = fields.Many2many(
        comodel_name='hr.hospital.patient',
        string='Patients',
        help='Patients to reassign',
    )
    change_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        help='Date of doctor reassignment',
    )
    change_reason = fields.Text(
        string='Reason for Change',
        required=True,
        help='Reason for changing the doctor',
    )

    @api.onchange('old_doctor_id')
    def _onchange_old_doctor_id(self):
        """Оновлює domain для пацієнтів при зміні старого лікаря"""
        if self.old_doctor_id:
            return {
                'domain': {
                    'patient_ids': [
                        ('doctor_id', '=', self.old_doctor_id.id)
                    ]
                }
            }
        return {
            'domain': {
                'patient_ids': []
            }
        }

    @api.model
    def default_get(self, fields_list):
        """Встановлює значення за замовчуванням з контексту"""
        res = super().default_get(fields_list)

        # Якщо викликано з list view пацієнтів, беремо вибраних пацієнтів
        if self.env.context.get('active_model') == 'hr.hospital.patient':
            active_ids = self.env.context.get('active_ids', [])
            if active_ids:
                res['patient_ids'] = [(6, 0, active_ids)]

                # Спробуємо визначити спільного лікаря
                patients = self.env['hr.hospital.patient'].browse(active_ids)
                doctors = patients.mapped('doctor_id')
                if len(doctors) == 1:
                    res['old_doctor_id'] = doctors.id

        return res

    def action_reassign(self):
        """Виконує масове перепризначення лікаря"""
        self.ensure_one()

        if not self.patient_ids:
            raise UserError(_('Please select at least one patient!'))

        if (self.old_doctor_id and
                self.new_doctor_id.id == self.old_doctor_id.id):
            raise UserError(
                _('New doctor must be different from old doctor!')
            )

        # Лічильник змінених пацієнтів
        changed_count = 0

        for patient in self.patient_ids:
            # Пропускаємо якщо новий лікар вже призначений
            if patient.doctor_id.id == self.new_doctor_id.id:
                continue

            # Оновлюємо лікаря пацієнта
            patient.write({
                'doctor_id': self.new_doctor_id.id,
            })

            # Оновлюємо історію (метод write в Patient автоматично це робить,
            # але якщо потрібно вказати дату та причину - робимо вручну)
            history = self.env['hr.hospital.patient.doctor.history'].search([
                ('patient_id', '=', patient.id),
                ('is_active', '=', True),
            ], limit=1)

            if history and history.doctor_id.id == self.new_doctor_id.id:
                # Оновлюємо причину зміни
                history.write({
                    'change_reason': self.change_reason,
                })
            elif history:
                # Закриваємо попередній запис з нашою датою та причиною
                history.write({
                    'change_date': self.change_date,
                    'is_active': False,
                    'change_reason': self.change_reason,
                })

            changed_count += 1

        # Повідомлення про успіх
        message = _(
            'Successfully reassigned %(count)d patient(s) '
            'to doctor %(doctor)s'
        ) % {
            'count': changed_count,
            'doctor': self.new_doctor_id.full_name,
        }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
