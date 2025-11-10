from odoo import fields, models


class HrHospitalContactPerson(models.Model):
    """Контактна особа - родич пацієнта, екстрений контакт тощо"""
    _name = 'hr.hospital.contact.person'
    _description = 'Hospital Contact Person'
    _inherit = ['abstract.person']
    _rec_name = 'full_name'

    # Успадковані поля з abstract.person:
    # - last_name, first_name, middle_name
    # - phone, email
    # - gender, date_of_birth
    # - age (computed), full_name (computed)
    # - country_id, lang_id
    # - image fields (з image.mixin)

    # Специфічні поля для контактної особи
    relationship = fields.Selection(
        selection=[
            ('spouse', 'Spouse'),
            ('parent', 'Parent'),
            ('child', 'Child'),
            ('sibling', 'Sibling'),
            ('friend', 'Friend'),
            ('colleague', 'Colleague'),
            ('other', 'Other'),
        ],
        help='Relationship to the patient',
    )
    is_emergency_contact = fields.Boolean(
        string='Emergency Contact',
        default=False,
        help='Mark as emergency contact',
    )
    notes = fields.Text(
        help='Additional information about the contact person',
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Related Patient',
        ondelete='cascade',
        help='Patient this contact person is related to',
    )
    active = fields.Boolean(
        default=True,
        help='Uncheck to archive the contact person',
    )
