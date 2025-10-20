from odoo import fields, models


class HrHospitalVisit(models.Model):
    _name = 'hr.hospital.visit'
    _description = 'Hospital Visit'

    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease',
    )
    visit_date = fields.Datetime(
        string='Visit Date',
        default=fields.Datetime.now,
        required=True,
    )
    notes = fields.Text(
        string='Notes',
    )
    diagnosis = fields.Text(
        string='Diagnosis',
    )
    prescription = fields.Text(
        string='Prescription',
    )