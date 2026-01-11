"""Tests for auto_monitoring models."""
from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError
from psycopg2 import IntegrityError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAutoMonitoringModels(TransactionCase):
    """Test suite for Auto Monitoring models."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.Vehicle = self.env['auto.monitoring.vehicle']
        self.TripPurpose = self.env['auto.monitoring.trip.purpose']
        self.Trip = self.env['auto.monitoring.trip']
        self.DBConnector = self.env['auto.monitoring.db.connector']

        # Create test vehicle
        self.vehicle = self.Vehicle.create({
            'imei': '123456789012345',
            'reg_number': 'AA1234BB',
            'vehicle_model': 'Toyota Camry',
            'fuel_card_number': 'CARD-001',
            'fuel_norm': 8.5,
        })

        # Create test trip purposes
        self.purpose_business = self.TripPurpose.create({
            'name_uk': 'Ділова поїздка',
            'code': 'business',
            'description': 'Поїздка по роботі',
            'is_active': True,
        })

        self.purpose_personal = self.TripPurpose.create({
            'name_uk': 'Особиста поїздка',
            'code': 'personal',
            'description': 'Особисті справи',
            'is_active': True,
        })

        self.purpose_other = self.TripPurpose.create({
            'name_uk': 'Інше',
            'code': 'other',
            'description': 'Інша мета',
            'is_active': True,
        })

    # Vehicle Tests

    def test_vehicle_name_get(self):
        """Test vehicle display_name shows registration and model."""
        name = self.vehicle.display_name
        self.assertIn('AA1234BB', name)
        self.assertIn('Toyota Camry', name)

    def test_vehicle_compute_last_known_location(self):
        """Test last known location computation."""
        self.vehicle.write({
            'last_latitude': 50.4501,
            'last_longitude': 30.5234,
        })
        self.assertEqual(self.vehicle.last_latitude, 50.4501)
        self.assertEqual(self.vehicle.last_longitude, 30.5234)

    def test_vehicle_imei_constraint(self):
        """Test vehicle IMEI uniqueness."""
        with self.assertRaises(
            IntegrityError,
            msg="Should not allow duplicate IMEI"
        ):
            self.Vehicle.create({
                'imei': '123456789012345',  # Same as self.vehicle
                'reg_number': 'BB5678CC',
                'vehicle_model': 'Honda Accord',
            })

    # Trip Purpose Tests

    def test_trip_purpose_name_get(self):
        """Test trip purpose display_name shows name."""
        name = self.purpose_business.display_name
        self.assertIn('Ділова поїздка', name)

    def test_trip_purpose_code_constraint(self):
        """Test trip purpose code uniqueness."""
        with self.assertRaises(
            IntegrityError,
            msg="Should not allow duplicate code"
        ):
            self.TripPurpose.create({
                'name_uk': 'Duplicate Business',
                'code': 'business',  # Same as self.purpose_business
            })

    def test_trip_purpose_sync_from_external_db(self):
        """Test syncing trip purposes from external DB."""
        mock_data = [
            {
                'id': 1,
                'name_uk': 'Test Purpose 1',
                'code': 'test1',
                'description': 'Test description 1',
                'is_active': True,
            },
            {
                'id': 2,
                'name_uk': 'Test Purpose 2',
                'code': 'test2',
                'description': 'Test description 2',
                'is_active': True,
            },
        ]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_data
        ):
            self.TripPurpose.sync_from_external_db()

            # Check if purposes were created/updated
            purpose1 = self.TripPurpose.search([('code', '=', 'test1')])
            self.assertTrue(purpose1, "Purpose with code 'test1' should exist")
            self.assertEqual(purpose1.name_uk, 'Test Purpose 1')

    # Trip Model Tests (now with _auto=True, records created directly)

    def _create_test_trip(self, **kwargs):
        """Helper to create test trip with defaults."""
        defaults = {
            'external_id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'route_description': 'Test route',
            'total_km': 100,
            'in_city_km': 60,
            'outside_city_km': 40,
            'fuel_liters': 8.5,
        }
        defaults.update(kwargs)
        return self.Trip.with_context(sync_mode=True).create(defaults)

    def test_trip_compute_vehicle_id(self):
        """Test vehicle computation from IMEI."""
        trip = self._create_test_trip()
        self.assertEqual(
            trip.vehicle_id.id,
            self.vehicle.id,
            "Vehicle should be computed from IMEI"
        )

    def test_trip_compute_is_editable(self):
        """Test trip editability based on deadline."""
        # Create trip with recent date (should be editable)
        recent_date = date.today() - timedelta(days=10)
        trip = self._create_test_trip(trip_date=recent_date)
        self.assertTrue(
            trip.is_editable,
            "Recent trip should be editable"
        )

    def test_trip_compute_is_manager(self):
        """Test is_manager computation."""
        manager_group = self.env.ref(
            'auto_monitoring.group_auto_monitoring_manager'
        )
        manager_user = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'groups_id': [(4, manager_group.id)],
        })

        trip = self._create_test_trip()
        trip_as_manager = trip.with_user(manager_user)
        self.assertTrue(
            trip_as_manager.is_manager,
            "Manager user should have is_manager=True"
        )

    def test_trip_write_editable_fields(self):
        """Test writing editable fields (trip_purpose, comment)."""
        trip = self._create_test_trip()

        # Mock external DB sync
        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=None
        ):
            trip.write({
                'trip_purpose_id': self.purpose_business.id,
                'user_comment': 'Test comment',
            })

        self.assertEqual(trip.trip_purpose_id.id, self.purpose_business.id)
        self.assertEqual(trip.user_comment, 'Test comment')

    def test_trip_write_non_editable_raises_error(self):
        """Test that writing to non-editable trip raises error."""
        old_date = date.today() - timedelta(days=60)
        trip = self._create_test_trip(trip_date=old_date)

        with self.assertRaises(
            UserError,
            msg="Should not allow editing past deadline"
        ):
            trip.write({
                'trip_purpose_id': self.purpose_business.id,
            })

    def test_trip_write_invalid_fields_raises_error(self):
        """Test that writing to non-editable fields raises error."""
        trip = self._create_test_trip()

        with self.assertRaises(
            UserError,
            msg="Should not allow editing read-only fields"
        ):
            trip.write({
                'total_km': 200,  # Read-only field
            })

    def test_trip_manager_can_edit_past_deadline(self):
        """Test that manager can edit trip past deadline."""
        manager_group = self.env.ref(
            'auto_monitoring.group_auto_monitoring_manager'
        )
        manager_user = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager_edit',
            'groups_id': [(4, manager_group.id)],
        })

        old_date = date.today() - timedelta(days=60)
        trip = self._create_test_trip(trip_date=old_date)
        trip_as_manager = trip.with_user(manager_user)

        # Manager should be able to write even if not editable
        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=None
        ):
            trip_as_manager.write({
                'trip_purpose_id': self.purpose_business.id,
            })

    def test_trip_compute_distance(self):
        """Test distance computation from in_city + outside_city."""
        trip = self._create_test_trip(in_city_km=60, outside_city_km=40)
        self.assertEqual(
            trip.distance,
            100.0,
            "Distance should equal in_city_km + outside_city_km"
        )

    def test_trip_compute_fuel_consumed(self):
        """Test fuel_consumed computation from fuel_liters."""
        trip = self._create_test_trip(fuel_liters=12.5)
        self.assertEqual(
            trip.fuel_consumed,
            12.5,
            "Fuel consumed should equal fuel_liters"
        )

    def test_trip_sync_from_external_db(self):
        """Test syncing trips from external DB."""
        mock_data = [
            {
                'id': 100,
                'imei': '123456789012345',
                'trip_date': date.today(),
                'route_description': 'Synced route',
                'in_city_km': 50,
                'outside_city_km': 30,
                'total_km': 80,
                'city_coefficient': 1.0,
                'outside_coefficient': 1.0,
                'fuel_liters': 7.0,
                'project_name': 'Test Project',
                'payment_type': 'cash',
                'driver_name': 'Test Driver',
                'trip_purpose_id': None,
                'trip_purpose_other': '',
                'user_comment': '',
                'start_time': None,
                'end_time': None,
                'start_address': 'Start',
                'end_address': 'End',
                'processed_at': None,
                'updated_at': None,
            },
        ]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_data
        ):
            synced = self.Trip.sync_from_external_db()
            self.assertEqual(synced, 1, "Should sync 1 trip")

            trip = self.Trip.search([('external_id', '=', 100)])
            self.assertTrue(trip, "Trip should exist after sync")
            self.assertEqual(trip.route_description, 'Synced route')
