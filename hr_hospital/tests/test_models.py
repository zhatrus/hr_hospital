"""Tests for hr_hospital models."""
from datetime import date, timedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHospitalModels(TransactionCase):
    """Test suite for Hospital models."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.Doctor = self.env['hr.hospital.doctor']
        self.Patient = self.env['hr.hospital.patient']
        self.Visit = self.env['hr.hospital.visit']
        self.Diagnosis = self.env['hr.hospital.diagnosis']
        self.Disease = self.env['hr.hospital.disease']
        self.PatientDoctorHistory = self.env[
            'hr.hospital.patient.doctor.history'
        ]

        self.specialization = self.env[
            'hr.hospital.doctor.specialization'
        ].create({
            'name': 'Therapist',
            'code': 'THER',
        })

        self.mentor_doctor = self.Doctor.create({
            'first_name': 'Senior',
            'last_name': 'Mentor',
            'license_number': 'LIC-MENTOR-001',
            'license_issue_date': date.today() - timedelta(days=3650),
            'specialization_id': self.specialization.id,
            'is_intern': False,
        })

        self.doctor = self.Doctor.create({
            'first_name': 'John',
            'last_name': 'Doe',
            'license_number': 'LIC-001',
            'license_issue_date': date.today() - timedelta(days=365),
            'specialization_id': self.specialization.id,
        })

        self.patient = self.Patient.create({
            'first_name': 'Jane',
            'last_name': 'Smith',
            'birth_date': date.today() - timedelta(days=10950),
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
        self.assertEqual(
            action['context']['default_patient_id'],
            self.patient.id,
        )
        self.assertIn(visit.id, self.Visit.search(action['domain']).ids)

    def test_diagnosis_compute_disease_type(self):
        """Test disease_type_id computation for hierarchical diseases."""
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

    # New tests for Module 3 methods

    def test_abstract_person_compute_age(self):
        """Test age computation from birth_date."""
        birth_date = date.today() - timedelta(days=10950)  # 30 years
        patient = self.Patient.create({
            'first_name': 'Test',
            'last_name': 'Patient',
            'birth_date': birth_date,
        })
        self.assertEqual(
            patient.age, 30,
            "Age should be computed correctly from birth_date"
        )

    def test_abstract_person_compute_full_name(self):
        """Test full_name computation from first, middle, last names."""
        patient = self.Patient.create({
            'first_name': 'John',
            'middle_name': 'Michael',
            'last_name': 'Doe',
        })
        self.assertEqual(
            patient.full_name, 'Doe John Michael',
            "Full name should combine last, first, and middle names"
        )

    def test_doctor_compute_years_of_experience(self):
        """Test years_of_experience computation from license_issue_date."""
        license_date = date.today() - timedelta(days=1825)  # 5 years
        doctor = self.Doctor.create({
            'first_name': 'Experienced',
            'last_name': 'Doctor',
            'license_number': 'LIC-EXP-001',
            'license_issue_date': license_date,
            'specialization_id': self.specialization.id,
        })
        self.assertEqual(
            doctor.years_of_experience, 5,
            "Years of experience should be 5 years"
        )

    def test_doctor_name_get_with_specialization(self):
        """Test name_get displays doctor name with specialization."""
        result = self.doctor.name_get()
        self.assertEqual(len(result), 1)
        name = result[0][1]
        self.assertIn('Doe John', name)
        self.assertIn('Therapist', name)

    def test_patient_write_creates_history(self):
        """Test that changing patient's doctor creates history record."""
        self.patient.write({'doctor_id': self.doctor.id})

        new_doctor = self.Doctor.create({
            'first_name': 'New',
            'last_name': 'Doctor',
            'license_number': 'LIC-NEW-001',
            'specialization_id': self.specialization.id,
        })

        self.patient.write({'doctor_id': new_doctor.id})

        history = self.PatientDoctorHistory.search([
            ('patient_id', '=', self.patient.id)
        ])
        self.assertTrue(
            len(history) >= 2,
            "History should be created when doctor changes"
        )

    def test_patient_doctor_history_create_deactivates_previous(self):
        """Test that creating new history deactivates previous record."""
        history1 = self.PatientDoctorHistory.create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'assignment_date': date.today() - timedelta(days=30),
        })

        self.assertTrue(
            history1.is_active,
            "First history record should be active"
        )

        new_doctor = self.Doctor.create({
            'first_name': 'Another',
            'last_name': 'Doctor',
            'license_number': 'LIC-ANOTHER-001',
            'specialization_id': self.specialization.id,
        })

        history2 = self.PatientDoctorHistory.create({
            'patient_id': self.patient.id,
            'doctor_id': new_doctor.id,
            'assignment_date': date.today(),
        })

        history1.invalidate_recordset()
        self.assertFalse(
            history1.is_active,
            "Previous history should be deactivated"
        )
        self.assertTrue(
            history2.is_active,
            "New history should be active"
        )

    def test_diagnosis_approve_method(self):
        """Test diagnosis approval method sets approved fields."""
        visit = self.Visit.create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
        })

        disease = self.Disease.create({
            'name': 'Test Disease',
        })

        diagnosis = self.Diagnosis.create({
            'patient_id': self.patient.id,
            'visit_id': visit.id,
            'disease_id': disease.id,
        })

        self.assertFalse(diagnosis.is_approved)

        diagnosis.action_approve()

        self.assertTrue(diagnosis.is_approved)
        self.assertEqual(diagnosis.approved_by_id, self.env.user.partner_id)
        self.assertTrue(diagnosis.approved_date)

    def test_visit_unlink_with_diagnoses_raises_error(self):
        """Test that deleting visit with diagnoses raises error."""
        visit = self.Visit.create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
        })

        disease = self.Disease.create({
            'name': 'Test Disease',
        })

        self.Diagnosis.create({
            'patient_id': self.patient.id,
            'visit_id': visit.id,
            'disease_id': disease.id,
        })

        with self.assertRaises(
            ValidationError,
            msg="Should not allow deleting visit with diagnoses"
        ):
            visit.unlink()

    def test_doctor_constraint_intern_cannot_be_mentor(self):
        """Test that intern cannot be assigned as mentor."""
        intern = self.Doctor.create({
            'first_name': 'Intern',
            'last_name': 'Doctor',
            'license_number': 'LIC-INTERN-001',
            'specialization_id': self.specialization.id,
            'is_intern': True,
        })

        with self.assertRaises(
            ValidationError,
            msg="Intern should not be allowed as mentor"
        ):
            self.Doctor.create({
                'first_name': 'Another',
                'last_name': 'Intern',
                'license_number': 'LIC-INTERN-002',
                'specialization_id': self.specialization.id,
                'is_intern': True,
                'mentor_id': intern.id,
            })

    def test_disease_recursive_hierarchy_constraint(self):
        """Test that recursive disease hierarchy is prevented."""
        disease1 = self.Disease.create({'name': 'Disease 1'})
        disease2 = self.Disease.create({
            'name': 'Disease 2',
            'parent_id': disease1.id,
        })

        with self.assertRaises(
            ValidationError,
            msg="Should not allow recursive hierarchy"
        ):
            disease1.write({'parent_id': disease2.id})
