import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AutoMonitoringVehicle(models.Model):
    """Vehicle model - represents transport vehicles from external DB.

    Syncs data from external 'vehicles' table and stores locally in Odoo
    for relationship management and extended functionality.
    """
    _name = 'auto.monitoring.vehicle'
    _description = 'Vehicle'
    _order = 'reg_number'
    _rec_name = 'display_name'

    external_id = fields.Integer(
        string='External ID',
        readonly=True,
        index=True,
        help='ID from external vehicles table',
    )
    imei = fields.Char(
        size=20,
        readonly=True,
        index=True,
        help='IMEI of GPS tracker',
    )
    serial_number = fields.Char(
        string='S/N',
        size=20,
        readonly=True,
        help='Serial number of GPS tracker',
    )
    reg_number = fields.Char(
        string='Registration Number',
        size=20,
        required=True,
        help='Vehicle registration number (plate)',
    )
    vehicle_model = fields.Char(
        string='Model',
        size=255,
        help='Vehicle make and model',
    )
    fuel_card_number = fields.Char(
        string='Fuel Card',
        size=32,
        help='Fuel card number for refueling',
    )
    fuel_norm = fields.Float(
        string='Fuel Norm (L/100km)',
        digits=(5, 2),
        default=10.0,
        help='Base fuel consumption norm in liters per 100 km',
    )
    sim_number = fields.Char(
        string='SIM Number',
        size=20,
        help='SIM card phone number in tracker',
    )
    alias = fields.Char(
        size=255,
        help='Friendly name / alias for the vehicle',
    )

    active = fields.Boolean(
        default=True,
    )

    last_latitude = fields.Float(
        string='Latitude',
        digits=(10, 6),
        readonly=True,
    )
    last_longitude = fields.Float(
        string='Longitude',
        digits=(10, 6),
        readonly=True,
    )
    last_speed = fields.Integer(
        string='Speed (km/h)',
        readonly=True,
    )
    last_fuel = fields.Float(
        string='Fuel Level (L)',
        digits=(10, 2),
        readonly=True,
    )
    last_odometer = fields.Float(
        string='Odometer (km)',
        digits=(12, 1),
        readonly=True,
    )
    last_update = fields.Datetime(
        string='Last Update',
        readonly=True,
    )
    last_address = fields.Char(
        string='Last Address',
        readonly=True,
    )

    status = fields.Selection(
        selection=[
            ('moving', 'Moving'),
            ('stopped', 'Stopped'),
            ('parked', 'Parked'),
            ('offline', 'Offline'),
        ],
        string='Status',
        compute='_compute_status',
        store=False,
    )

    tracker_data_ids = fields.One2many(
        comodel_name='auto.monitoring.tracker.data',
        inverse_name='vehicle_id',
        string='Tracker Data',
    )
    fuel_transaction_ids = fields.One2many(
        comodel_name='auto.monitoring.fuel.transaction',
        inverse_name='vehicle_id',
        string='Fuel Transactions',
    )
    trip_ids = fields.One2many(
        comodel_name='auto.monitoring.trip',
        inverse_name='vehicle_id',
        string='Trips',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    _sql_constraints = [
        ('imei_unique', 'UNIQUE(imei)', 'IMEI must be unique!'),
        ('external_id_unique', 'UNIQUE(external_id)',
         'External ID must be unique!'),
    ]

    @api.depends('reg_number', 'alias', 'vehicle_model')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.reg_number or '']
            if rec.alias:
                parts.append(f"({rec.alias})")
            elif rec.vehicle_model:
                parts.append(f"- {rec.vehicle_model}")
            rec.display_name = ' '.join(parts)

    @api.depends('last_speed', 'last_update')
    def _compute_status(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.last_update:
                rec.status = 'offline'
            elif (now - rec.last_update).total_seconds() > 3600:
                rec.status = 'offline'
            elif rec.last_speed and rec.last_speed > 3:
                rec.status = 'moving'
            elif rec.last_speed == 0:
                rec.status = 'parked'
            else:
                rec.status = 'stopped'

    @api.model
    def sync_from_external_db(self):
        """Sync vehicles from external database."""
        connector = self.env['auto.monitoring.db.connector']

        query = """
            SELECT id, imei, s_n, reg_number, vehicle_model,
                   fuel_card_number, fuel_norm_l_100km, sim_number, alias
            FROM vehicles
            ORDER BY id
        """

        rows = connector.execute_query(query)
        if not rows:
            _logger.warning(
                "No vehicles found in external DB or connection error"
            )
            return

        synced = 0
        for row in rows:
            vals = {
                'external_id': row.get('id'),
                'imei': row.get('imei'),
                'serial_number': row.get('s_n'),
                'reg_number': (
                    row.get('reg_number') or f"UNKNOWN-{row.get('id')}"
                ),
                'vehicle_model': row.get('vehicle_model'),
                'fuel_card_number': row.get('fuel_card_number'),
                'fuel_norm': row.get('fuel_norm_l_100km') or 10.0,
                'sim_number': row.get('sim_number'),
                'alias': row.get('alias'),
            }

            existing = self.search(
                [('external_id', '=', row.get('id'))], limit=1
            )
            if existing:
                existing.write(vals)
            else:
                self.create(vals)
            synced += 1

        _logger.info("Synced %d vehicles from external DB", synced)
        return synced

    @api.model
    def update_last_positions(self):
        """Update last known positions for all vehicles from tracker_light."""
        connector = self.env['auto.monitoring.db.connector']

        query = """
            SELECT DISTINCT ON (imei)
                imei, latitude, longitude, speed, fuel, odometer,
                timestamp, address_display_name
            FROM tracker_light
            WHERE imei IS NOT NULL
            ORDER BY imei, timestamp DESC
        """

        rows = connector.execute_query(query)
        if not rows:
            return

        for row in rows:
            vehicle = self.search([('imei', '=', row.get('imei'))], limit=1)
            if vehicle:
                vehicle.write({
                    'last_latitude': row.get('latitude'),
                    'last_longitude': row.get('longitude'),
                    'last_speed': row.get('speed') or 0,
                    'last_fuel': row.get('fuel'),
                    'last_odometer': (row.get('odometer') or 0) / 1000.0,
                    'last_update': row.get('timestamp'),
                    'last_address': row.get('address_display_name'),
                })

    def action_refresh_position(self):
        """Refresh position for selected vehicles."""
        self.update_last_positions()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Position Updated'),
                'message': _('Vehicle positions have been refreshed'),
                'type': 'success',
            }
        }

    def action_view_on_map(self):
        """Open map view centered on this vehicle."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': (f'https://www.openstreetmap.org/'
                    f'?mlat={self.last_latitude}&mlon={self.last_longitude}'
                    f'&zoom=15'),
            'target': 'new',
        }
