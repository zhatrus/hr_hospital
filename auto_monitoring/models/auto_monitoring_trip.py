import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AutoMonitoringTrip(models.Model):
    """Trip model - calculated trips based on tracker data.

    Trips are computed from tracker_light data by analyzing
    movement patterns and stops.
    """
    _name = 'auto.monitoring.trip'
    _description = 'Trip'
    _order = 'start_time desc'

    vehicle_id = fields.Many2one(
        comodel_name='auto.monitoring.vehicle',
        string='Vehicle',
        required=True,
        index=True,
        ondelete='cascade',
    )

    start_time = fields.Datetime(
        string='Start Time',
        required=True,
    )
    end_time = fields.Datetime(
        string='End Time',
    )

    start_address = fields.Char(
        string='Start Location',
    )
    end_address = fields.Char(
        string='End Location',
    )

    start_latitude = fields.Float(digits=(10, 6))
    start_longitude = fields.Float(digits=(10, 6))
    end_latitude = fields.Float(digits=(10, 6))
    end_longitude = fields.Float(digits=(10, 6))

    distance = fields.Float(
        string='Distance (km)',
        digits=(10, 1),
    )

    duration = fields.Float(
        string='Duration (hours)',
        digits=(10, 2),
        compute='_compute_duration',
        store=True,
    )
    duration_display = fields.Char(
        string='Duration',
        compute='_compute_duration_display',
    )

    max_speed = fields.Integer(
        string='Max Speed (km/h)',
    )
    avg_speed = fields.Float(
        string='Avg Speed (km/h)',
        digits=(5, 1),
        compute='_compute_avg_speed',
        store=True,
    )

    fuel_consumed = fields.Float(
        string='Fuel Consumed (L)',
        digits=(10, 2),
    )

    status = fields.Selection(
        selection=[
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ],
        default='in_progress',
    )

    speed_violation = fields.Boolean(
        string='Speed Violation',
        compute='_compute_speed_violation',
        store=True,
    )

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0

    @api.depends('duration')
    def _compute_duration_display(self):
        for rec in self:
            if rec.duration:
                hours = int(rec.duration)
                minutes = int((rec.duration - hours) * 60)
                rec.duration_display = f"{hours}год {minutes}хв"
            else:
                rec.duration_display = '-'

    @api.depends('distance', 'duration')
    def _compute_avg_speed(self):
        for rec in self:
            if rec.duration and rec.duration > 0:
                rec.avg_speed = rec.distance / rec.duration
            else:
                rec.avg_speed = 0

    @api.depends('max_speed')
    def _compute_speed_violation(self):
        for rec in self:
            rec.speed_violation = rec.max_speed and rec.max_speed > 130

    @api.model
    def calculate_trips_for_vehicle(self, vehicle_id, date_from=None,
                                     date_to=None):
        """Calculate trips for a vehicle based on tracker data.

        A trip starts when ignition turns on OR speed > 0 after stopped.
        A trip ends when ignition turns off OR speed = 0 for > 5 minutes.
        """
        vehicle = self.env['auto.monitoring.vehicle'].browse(vehicle_id)
        if not vehicle or not vehicle.imei:
            return []

        connector = self.env['auto.monitoring.db.connector']

        if not date_from:
            date_from = fields.Datetime.now() - timedelta(days=1)
        if not date_to:
            date_to = fields.Datetime.now()

        query = """
            SELECT id, latitude, longitude, speed, ignition, odometer,
                   timestamp, address_display_name
            FROM tracker_light
            WHERE imei = %s AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """

        data = connector.execute_query(
            query, (vehicle.imei, date_from, date_to)
        )
        if not data:
            return []

        trips = []
        current_trip = None
        last_moving_point = None
        stop_start = None

        STOP_THRESHOLD_MINUTES = 5

        for point in data:
            speed = point.get('speed', 0) or 0
            ignition = point.get('ignition', False)
            timestamp = point.get('timestamp')

            is_moving = speed > 3 or ignition

            if is_moving:
                if current_trip is None:
                    current_trip = {
                        'vehicle_id': vehicle.id,
                        'start_time': timestamp,
                        'start_latitude': point.get('latitude'),
                        'start_longitude': point.get('longitude'),
                        'start_address': point.get('address_display_name'),
                        'start_odometer': point.get('odometer', 0) / 1000.0,
                        'max_speed': speed,
                    }
                    stop_start = None
                else:
                    stop_start = None
                    if speed > current_trip.get('max_speed', 0):
                        current_trip['max_speed'] = speed

                last_moving_point = point

            else:
                if current_trip is not None:
                    if stop_start is None:
                        stop_start = timestamp
                    else:
                        stop_duration = (
                            (timestamp - stop_start).total_seconds() / 60
                        )
                        if stop_duration >= STOP_THRESHOLD_MINUTES:
                            current_trip['end_time'] = stop_start
                            if last_moving_point:
                                current_trip['end_latitude'] = (
                                    last_moving_point.get('latitude')
                                )
                                current_trip['end_longitude'] = (
                                    last_moving_point.get('longitude')
                                )
                                current_trip['end_address'] = (
                                    last_moving_point.get('address_display_name')
                                )
                                end_odometer = (
                                    last_moving_point.get('odometer', 0) / 1000.0
                                )
                            else:
                                current_trip['end_latitude'] = None
                                current_trip['end_longitude'] = None
                                current_trip['end_address'] = None
                                end_odometer = 0
                            start_odo = current_trip.get('start_odometer', 0)
                            current_trip['distance'] = end_odometer - start_odo
                            current_trip['status'] = 'completed'

                            del current_trip['start_odometer']
                            trips.append(current_trip)

                            current_trip = None
                            stop_start = None

        if current_trip is not None and last_moving_point:
            current_trip['end_time'] = last_moving_point.get('timestamp')
            current_trip['end_latitude'] = last_moving_point.get('latitude')
            current_trip['end_longitude'] = last_moving_point.get('longitude')
            current_trip['end_address'] = (
                last_moving_point.get('address_display_name')
            )
            end_odometer = last_moving_point.get('odometer', 0) / 1000.0
            start_odo = current_trip.get('start_odometer', 0)
            current_trip['distance'] = end_odometer - start_odo
            current_trip['status'] = 'in_progress'
            del current_trip['start_odometer']
            trips.append(current_trip)

        return trips

    @api.model
    def sync_trips_for_vehicle(self, vehicle_id, date_from=None,
                                date_to=None):
        """Calculate and save trips for a vehicle."""
        trips_data = self.calculate_trips_for_vehicle(
            vehicle_id, date_from, date_to
        )

        created_trips = []
        for trip_vals in trips_data:
            existing = self.search([
                ('vehicle_id', '=', vehicle_id),
                ('start_time', '=', trip_vals['start_time']),
            ], limit=1)

            if existing:
                existing.write(trip_vals)
                created_trips.append(existing)
            else:
                created_trips.append(self.create(trip_vals))

        return created_trips

    @api.model
    def sync_all_trips(self, date_from=None, date_to=None):
        """Sync trips for all active vehicles."""
        vehicles = self.env['auto.monitoring.vehicle'].search(
            [('active', '=', True)]
        )
        total_trips = 0

        for vehicle in vehicles:
            trips = self.sync_trips_for_vehicle(vehicle.id, date_from, date_to)
            total_trips += len(trips)

        _logger.info(
            "Synced %d trips for %d vehicles", total_trips, len(vehicles)
        )
        return total_trips
