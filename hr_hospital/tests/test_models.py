from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHospitalModels(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Doctor = self.env['hr.hospital.doctor']
        self.Patient = self.env['hr.hospital.patient']
        self.Visit = self.env['hr.hospital.visit']
        self.Diagnosis = self.env['hr.hospital.diagnosis']
        self.specialization = self.env[
            'hr.hospital.doctor.specialization'
        ].create({'name': 'Therapist'})
        self.doctor = self.Doctor.create({
            'first_name': 'John',
            'last_name': 'Doe',
            'license_number': 'LIC-001',
            'specialization_id': self.specialization.id,
        })
        self.patient = self.Patient.create({
            'first_name': 'Jane',
            'last_name': 'Smith',
        })

    def test_visit_compute_visit_date(self):
        scheduled = fields.Datetime.now()
        visit = self.Visit.create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'scheduled_date': scheduled,
        })
        self.assertEqual(
            visit.visit_date, visit.scheduled_date,
            "visit_date should mirror scheduled_date via compute",
        )

    def test_patient_action_view_visits_domain(self):
        visit = self.Visit.create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
        })
        action = self.patient.action_view_visits()
        self.assertIn(('patient_id', '=', self.patient.id), action['domain'])
        self.assertEqual(action['context']['default_patient_id'], self.patient.id)
        self.assertIn(visit.id, self.Visit.search(action['domain']).ids)

    def test_diagnosis_compute_disease_type(self):
        parent_disease = self.env['hr.hospital.disease'].create({
            'name': 'Infection',
        })
        child_disease = self.env['hr.hospital.disease'].create({
            'name': 'Flu',
            'parent_id': parent_disease.id,
        })
        visit = self.Visit.create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
        })
        diagnosis = self.Diagnosis.create({
            'patient_id': self.patient.id,
            'visit_id': visit.id,
            'disease_id': child_disease.id,
        })
        self.assertEqual(
            diagnosis.disease_type_id, parent_disease,
            "disease_type_id should fall back to parent disease",
        )
