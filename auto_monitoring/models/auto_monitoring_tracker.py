import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AutoMonitoringTrackerData(models.Model):
    """Tracker Data model - GPS tracking points from external DB.
    
    This is a read-only model that fetches data from external 'tracker_light' table.
    Data is not stored in Odoo DB, only displayed.
    """
    _name = 'auto.monitoring.tracker.data'
    _description = 'Tracker Data'
    _order = 'timestamp desc'
    _auto = False

    id = fields.Integer(readonly=True)
    vehicle_id = fields.Many2one(
        comodel_name='auto.monitoring.vehicle',
        string='Vehicle',
        compute='_compute_vehicle_id',
        store=False,
    )
    imei = fields.Char(size=20, readonly=True)
    latitude = fields.Float(digits=(10, 6), readonly=True)
    longitude = fields.Float(digits=(10, 6), readonly=True)
    speed = fields.Integer(readonly=True)
    satellites = fields.Integer(readonly=True)
    angle = fields.Integer(readonly=True)
    odometer = fields.Float(
        string='Odometer (km)',
        digits=(12, 1),
        readonly=True,
    )
    ignition = fields.Boolean(readonly=True)
    fuel = fields.Float(digits=(10, 2), readonly=True)
    rpm = fields.Integer(readonly=True)
    device_battery = fields.Float(readonly=True)
    temperature = fields.Float(readonly=True)
    battery = fields.Integer(readonly=True)
    timestamp = fields.Datetime(readonly=True)
    created_at = fields.Datetime(readonly=True)
    
    address_place = fields.Char(readonly=True)
    address_city = fields.Char(readonly=True)
    address_road = fields.Char(readonly=True)
    address_display_name = fields.Char(
        string='Address',
        readonly=True,
    )

    in_city = fields.Boolean(
        string='In City',
        compute='_compute_in_city',
        store=False,
    )

    @api.depends('imei')
    def _compute_vehicle_id(self):
        Vehicle = self.env['auto.monitoring.vehicle']
        for rec in self:
            vehicle = Vehicle.search([('imei', '=', rec.imei)], limit=1)
            rec.vehicle_id = vehicle.id if vehicle else False

    def _compute_in_city(self):
        for rec in self:
            rec.in_city = bool(rec.address_city or rec.address_place)

    def init(self):
        """Create view for tracker data from external DB."""
        pass

    @api.model
    def _fetch_tracker_data(self, domain=None, limit=100, offset=0):
        """Fetch tracker data from external database.
        
        Args:
            domain: List of filter conditions
            limit: Max number of records
            offset: Offset for pagination
            
        Returns:
            List of tracker data dicts
        """
        connector = self.env['auto.monitoring.db.connector']
        
        where_clauses = ["1=1"]
        params = []
        
        if domain:
            for condition in domain:
                field, operator, value = condition
                if field == 'imei' and operator == '=':
                    where_clauses.append("imei = %s")
                    params.append(value)
                elif field == 'timestamp' and operator == '>=':
                    where_clauses.append("timestamp >= %s")
                    params.append(value)
                elif field == 'timestamp' and operator == '<=':
                    where_clauses.append("timestamp <= %s")
                    params.append(value)
                elif field == 'speed' and operator == '>':
                    where_clauses.append("speed > %s")
                    params.append(value)
        
        query = f"""
            SELECT id, imei, latitude, longitude, speed, satellites, angle,
                   odometer / 1000.0 as odometer, 
                   CASE WHEN ignition = 1 THEN true ELSE false END as ignition,
                   fuel, rpm, device_battery, temperature, battery,
                   timestamp, created_at,
                   address_place, address_city, address_road, address_display_name
            FROM tracker_light
            WHERE {' AND '.join(where_clauses)}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        return connector.execute_query(query, tuple(params))

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override to fetch data from external DB."""
        limit = limit or 100
        data = self._fetch_tracker_data(domain, limit, offset)
        
        if fields:
            return [{k: v for k, v in row.items() if k in fields or k == 'id'} for row in data]
        return data

    @api.model
    def get_latest_by_vehicle(self, vehicle_id):
        """Get latest tracker data for a specific vehicle."""
        vehicle = self.env['auto.monitoring.vehicle'].browse(vehicle_id)
        if not vehicle or not vehicle.imei:
            return None
        
        data = self._fetch_tracker_data([('imei', '=', vehicle.imei)], limit=1)
        return data[0] if data else None

    @api.model
    def get_speed_violations(self, speed_limit=130, hours=24):
        """Get speed violations above specified limit in last N hours."""
        connector = self.env['auto.monitoring.db.connector']
        
        since = fields.Datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT t.id, t.imei, t.speed, t.timestamp, t.address_display_name,
                   v.reg_number
            FROM tracker_light t
            LEFT JOIN vehicles v ON t.imei = v.imei
            WHERE t.speed > %s AND t.timestamp >= %s
            ORDER BY t.timestamp DESC
            LIMIT 100
        """
        
        return connector.execute_query(query, (speed_limit, since))

    @api.model
    def get_dashboard_stats(self):
        """Get statistics for dashboard."""
        connector = self.env['auto.monitoring.db.connector']
        Vehicle = self.env['auto.monitoring.vehicle']
        
        total_vehicles = Vehicle.search_count([('active', '=', True)])
        
        now = fields.Datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        query_moving = """
            SELECT COUNT(DISTINCT imei) as cnt
            FROM tracker_light
            WHERE timestamp >= %s AND speed > 3
        """
        result = connector.execute_query(query_moving, (one_hour_ago,), fetchall=False)
        moving_count = result.get('cnt', 0) if result else 0
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        query_violations = """
            SELECT COUNT(*) as cnt
            FROM tracker_light
            WHERE timestamp >= %s AND speed > 130
        """
        result = connector.execute_query(query_violations, (today_start,), fetchall=False)
        violations_count = result.get('cnt', 0) if result else 0
        
        query_mileage = """
            SELECT SUM(daily_mileage) as total_km
            FROM (
                SELECT imei, 
                       (MAX(odometer) - MIN(odometer)) / 1000.0 as daily_mileage
                FROM tracker_light
                WHERE timestamp >= %s
                GROUP BY imei
            ) sub
        """
        result = connector.execute_query(query_mileage, (today_start,), fetchall=False)
        today_mileage = round(result.get('total_km', 0) or 0, 1) if result else 0
        
        return {
            'total_vehicles': total_vehicles,
            'moving_count': moving_count,
            'parked_count': total_vehicles - moving_count,
            'violations_count': violations_count,
            'today_mileage': today_mileage,
        }
