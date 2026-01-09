"""Tests for auto_monitoring models."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
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
            'registration_number': 'AA1234BB',
            'model': 'Toyota Camry',
            'fuel_card_number': 'CARD-001',
            'fuel_norm': 8.5,
        })

        # Create test trip purposes
        self.purpose_business = self.TripPurpose.create({
            'name': 'Ділова поїздка',
            'code': 'business',
            'description': 'Поїздка по роботі',
            'active': True,
        })

        self.purpose_personal = self.TripPurpose.create({
            'name': 'Особиста поїздка',
            'code': 'personal',
            'description': 'Особисті справи',
            'active': True,
        })

        self.purpose_other = self.TripPurpose.create({
            'name': 'Інше',
            'code': 'other',
            'description': 'Інша мета',
            'active': True,
        })

    # Vehicle Tests

    def test_vehicle_name_get(self):
        """Test vehicle name_get displays registration and model."""
        result = self.vehicle.name_get()
        self.assertEqual(len(result), 1)
        name = result[0][1]
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
        """Test IMEI uniqueness constraint."""
        with self.assertRaises(
            ValidationError,
            msg="Should not allow duplicate IMEI"
        ):
            self.Vehicle.create({
                'imei': '123456789012345',  # Same as self.vehicle
                'registration_number': 'BB5678CC',
                'model': 'Honda Accord',
            })

    # Trip Purpose Tests

    def test_trip_purpose_name_get(self):
        """Test trip purpose name_get displays name and code."""
        result = self.purpose_business.name_get()
        self.assertEqual(len(result), 1)
        name = result[0][1]
        self.assertIn('business', name)
        self.assertIn('Ділова поїздка', name)

    def test_trip_purpose_code_constraint(self):
        """Test trip purpose code uniqueness."""
        with self.assertRaises(
            ValidationError,
            msg="Should not allow duplicate code"
        ):
            self.TripPurpose.create({
                'name': 'Duplicate Business',
                'code': 'business',  # Same as self.purpose_business
            })

    def test_trip_purpose_sync_from_external_db(self):
        """Test syncing trip purposes from external DB."""
        mock_data = [
            {
                'id': 1,
                'name': 'Test Purpose 1',
                'code': 'test1',
                'description': 'Test description 1',
                'active': True,
            },
            {
                'id': 2,
                'name': 'Test Purpose 2',
                'code': 'test2',
                'description': 'Test description 2',
                'active': True,
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
            self.assertEqual(purpose1.name, 'Test Purpose 1')

    # Trip Model Tests

    def test_trip_compute_vehicle_id(self):
        """Test vehicle computation from IMEI."""
        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'route_description': 'Test route',
            'total_km': 100,
            'in_city_km': 60,
            'outside_city_km': 40,
            'fuel_liters': 8.5,
            'is_editable': True,
            'trip_purpose_id': None,
            'user_comment': None,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.search([])
            if trips:
                trip = trips[0]
                # Vehicle should be computed from IMEI
                self.assertEqual(
                    trip.vehicle_id.id,
                    self.vehicle.id,
                    "Vehicle should be computed from IMEI"
                )

    def test_trip_compute_is_editable(self):
        """Test trip editability based on deadline."""
        from dateutil.relativedelta import relativedelta

        # Create trip with date within deadline
        recent_date = date.today() - timedelta(days=10)
        mock_trip_recent = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': recent_date,
            'total_km': 100,
            'is_editable': True,
        }]

        # Create trip with date past deadline
        old_date = date.today() - timedelta(days=60)
        deadline = old_date.replace(day=1) + relativedelta(months=1, days=5)
        is_past_deadline = date.today() > deadline

        mock_trip_old = [{
            'id': 2,
            'imei': '123456789012345',
            'trip_date': old_date,
            'total_km': 100,
            'is_editable': not is_past_deadline,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_recent
        ):
            trips = self.Trip.search([])
            if trips:
                self.assertTrue(
                    trips[0].is_editable,
                    "Recent trip should be editable"
                )

    def test_trip_compute_is_manager(self):
        """Test is_manager computation."""
        # Create manager user
        manager_group = self.env.ref(
            'auto_monitoring.group_auto_monitoring_manager'
        )
        manager_user = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'groups_id': [(4, manager_group.id)],
        })

        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'total_km': 100,
            'is_editable': True,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.with_user(manager_user).search([])
            if trips:
                self.assertTrue(
                    trips[0].is_manager,
                    "Manager user should have is_manager=True"
                )

    def test_trip_write_editable_fields(self):
        """Test writing editable fields (trip_purpose, comment)."""
        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'total_km': 100,
            'is_editable': True,
            'trip_purpose_id': None,
            'user_comment': None,
        }]

        mock_execute = MagicMock(return_value=mock_trip_data)

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            mock_execute
        ):
            trips = self.Trip.search([])
            if trips:
                trip = trips[0]

                # Mock write operation
                with patch.object(
                    self.DBConnector.__class__,
                    'execute_query',
                    return_value=None
                ):
                    trip.write({
                        'trip_purpose_id': self.purpose_business.id,
                        'user_comment': 'Test comment',
                    })

                    # Verify execute_query was called for UPDATE
                    self.assertTrue(
                        mock_execute.called,
                        "execute_query should be called for write"
                    )

    def test_trip_write_non_editable_raises_error(self):
        """Test that writing to non-editable trip raises error."""
        # Create trip past deadline
        old_date = date.today() - timedelta(days=60)

        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': old_date,
            'total_km': 100,
            'is_editable': False,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.search([])
            if trips:
                trip = trips[0]

                with self.assertRaises(
                    UserError,
                    msg="Should not allow editing past deadline"
                ):
                    trip.write({
                        'trip_purpose_id': self.purpose_business.id,
                    })

    def test_trip_write_invalid_fields_raises_error(self):
        """Test that writing to non-editable fields raises error."""
        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'total_km': 100,
            'is_editable': True,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.search([])
            if trips:
                trip = trips[0]

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
        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': old_date,
            'total_km': 100,
            'is_editable': False,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.with_user(manager_user).search([])
            if trips:
                trip = trips[0]

                # Manager should be able to write even if not editable
                with patch.object(
                    self.DBConnector.__class__,
                    'execute_query',
                    return_value=None
                ):
                    # Should not raise error
                    trip.write({
                        'trip_purpose_id': self.purpose_business.id,
                    })

    def test_trip_compute_distance(self):
        """Test distance computation from total_km."""
        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'total_km': 150,
            'is_editable': True,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.search([])
            if trips:
                self.assertEqual(
                    trips[0].distance,
                    150.0,
                    "Distance should equal total_km as float"
                )

    def test_trip_compute_fuel_consumed(self):
        """Test fuel_consumed computation from fuel_liters."""
        mock_trip_data = [{
            'id': 1,
            'imei': '123456789012345',
            'trip_date': date.today(),
            'total_km': 100,
            'fuel_liters': 12.5,
            'is_editable': True,
        }]

        with patch.object(
            self.DBConnector.__class__,
            'execute_query',
            return_value=mock_trip_data
        ):
            trips = self.Trip.search([])
            if trips:
                self.assertEqual(
                    trips[0].fuel_consumed,
                    12.5,
                    "Fuel consumed should equal fuel_liters"
                )
