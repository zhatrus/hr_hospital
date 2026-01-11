"""Auto Monitoring Trip model - synced from external database."""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AutoMonitoringTrip(models.Model):
    """Trip model - synced from external tracker_trips table.

    Data is synchronized from external 'tracker_trips' table to local Odoo DB.
    This approach ensures full compatibility with Odoo's ORM and web client.
    """
    _name = 'auto.monitoring.trip'
    _description = 'Trip'
    _order = 'trip_date desc, id desc'
    # _auto = True (default) - creates table in Odoo DB

    external_id = fields.Integer(
        string='External ID',
        readonly=True,
        index=True,
        help='ID from external tracker_trips table',
    )

    vehicle_id = fields.Many2one(
        comodel_name='auto.monitoring.vehicle',
        string='Vehicle',
        compute='_compute_vehicle_id',
        store=True,
        index=True,
    )
    imei = fields.Char(
        string='IMEI',
        size=20,
        readonly=True,
        index=True,
    )

    trip_date = fields.Date(
        string='Trip Date',
        readonly=True,
        index=True,
    )
    start_time = fields.Datetime(
        string='Start Time',
        readonly=True,
    )
    end_time = fields.Datetime(
        string='End Time',
        readonly=True,
    )

    route_description = fields.Text(
        string='Route Description',
        readonly=True,
    )
    start_address = fields.Text(
        string='Start Location',
        readonly=True,
    )
    end_address = fields.Text(
        string='End Location',
        readonly=True,
    )

    # Mileage fields
    in_city_km = fields.Integer(
        string='In City (km)',
        readonly=True,
    )
    outside_city_km = fields.Integer(
        string='Outside City (km)',
        readonly=True,
    )
    total_km = fields.Integer(
        string='Total Distance (km)',
        readonly=True,
    )
    distance = fields.Float(
        string='Distance (km)',
        compute='_compute_distance',
        store=True,
    )

    # Coefficients
    city_coefficient = fields.Float(
        string='City Coefficient',
        digits=(5, 2),
        readonly=True,
    )
    outside_coefficient = fields.Float(
        string='Outside Coefficient',
        digits=(5, 2),
        readonly=True,
    )

    # Fuel
    fuel_liters = fields.Float(
        string='Fuel (L)',
        digits=(10, 2),
        readonly=True,
    )
    fuel_consumed = fields.Float(
        string='Fuel Consumed (L)',
        compute='_compute_fuel_consumed',
        store=True,
    )

    # Trip details
    project_name = fields.Char(
        string='Project',
        size=255,
        readonly=True,
    )
    payment_type = fields.Char(
        string='Payment Type',
        size=50,
        readonly=True,
    )
    driver_name = fields.Char(
        string='Driver',
        size=255,
        readonly=True,
    )

    # Editable fields
    trip_purpose_id = fields.Many2one(
        comodel_name='auto.monitoring.trip.purpose',
        string='Trip Purpose',
        ondelete='set null',
    )
    trip_purpose_other = fields.Text(
        string='Purpose (Other)',
        help='Description when purpose is "Other"',
    )
    user_comment = fields.Text(
        string='User Comment',
    )

    # Status fields
    is_editable = fields.Boolean(
        string='Is Editable',
        compute='_compute_is_editable',
        store=False,
        help='Whether the trip can be edited by regular users',
    )
    is_manager = fields.Boolean(
        string='Is Manager',
        compute='_compute_is_manager',
        store=False,
    )

    # Timestamps
    processed_at = fields.Datetime(
        string='Processed At',
        readonly=True,
    )
    updated_at = fields.Datetime(
        string='Updated At',
        readonly=True,
    )
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True,
        help='When this record was last synced from external DB',
    )

    _sql_constraints = [
        ('external_id_unique', 'UNIQUE(external_id)',
         'External ID must be unique!'),
    ]

    @api.depends('imei')
    def _compute_vehicle_id(self):
        """Compute vehicle from IMEI."""
        Vehicle = self.env['auto.monitoring.vehicle']
        for rec in self:
            if rec.imei:
                vehicle = Vehicle.search([('imei', '=', rec.imei)], limit=1)
                rec.vehicle_id = vehicle.id if vehicle else False
            else:
                rec.vehicle_id = False

    @api.depends('in_city_km', 'outside_city_km')
    def _compute_distance(self):
        """Compute total distance."""
        for rec in self:
            rec.distance = (rec.in_city_km or 0) + (rec.outside_city_km or 0)

    @api.depends('fuel_liters')
    def _compute_fuel_consumed(self):
        """Compute fuel consumed."""
        for rec in self:
            rec.fuel_consumed = rec.fuel_liters or 0.0

    @api.depends('trip_date')
    def _compute_is_editable(self):
        """Check if trip can be edited based on deadline.

        Deadline: end of trip month + 5 days of next month.
        After deadline, only manager/admin can edit.
        """
        from dateutil.relativedelta import relativedelta
        today = fields.Date.today()

        for rec in self:
            if not rec.trip_date:
                rec.is_editable = False
                continue

            # Calculate deadline
            deadline = rec.trip_date.replace(day=1) + relativedelta(
                months=1, days=5
            )
            rec.is_editable = today <= deadline

    def _compute_is_manager(self):
        """Check if current user is manager or admin."""
        is_manager = self.env.user.has_group(
            'auto_monitoring.group_auto_monitoring_manager'
        )
        for rec in self:
            rec.is_manager = is_manager

    def write(self, vals):
        """Override write to sync changes back to external DB."""
        # Check which fields can be edited
        editable_fields = {'trip_purpose_id', 'trip_purpose_other',
                          'user_comment'}
        updating_fields = set(vals.keys())

        # Check if trying to update non-editable fields
        non_editable = updating_fields - editable_fields
        if non_editable:
            raise UserError(_(
                "Cannot modify fields: %s. "
                "Only trip purpose and comments can be edited."
            ) % ', '.join(non_editable))

        # Check editability for non-managers
        for rec in self:
            if not rec.is_editable and not rec.is_manager:
                raise UserError(_(
                    "Trip from %s cannot be edited. "
                    "Editing deadline has passed."
                ) % rec.trip_date)

        # Write to Odoo DB
        result = super().write(vals)

        # Sync changes to external DB
        self._sync_to_external_db(vals)

        return result

    def _sync_to_external_db(self, vals):
        """Sync changes to external database."""
        connector = self.env['auto.monitoring.db.connector']

        for rec in self:
            if not rec.external_id:
                continue

            update_parts = []
            params = []

            if 'trip_purpose_id' in vals:
                update_parts.append("trip_purpose_id = %s")
                params.append(vals['trip_purpose_id'] or None)

            if 'trip_purpose_other' in vals:
                update_parts.append("trip_purpose_other = %s")
                params.append(vals['trip_purpose_other'] or None)

            if 'user_comment' in vals:
                update_parts.append("user_comment = %s")
                params.append(vals['user_comment'] or None)

            if not update_parts:
                continue

            update_parts.append("updated_at = CURRENT_TIMESTAMP")
            params.append(rec.external_id)

            query = f"""
                UPDATE tracker_trips
                SET {', '.join(update_parts)}
                WHERE id = %s
            """

            try:
                connector.execute_query(query, tuple(params), fetchall=False)
            except Exception as e:
                _logger.error("Failed to sync trip %s to external DB: %s",
                             rec.external_id, e)

    @api.model
    def sync_from_external_db(self):
        """Sync trips from external database to Odoo.

        This method fetches all trips from external DB and creates/updates
        them in Odoo's local database.
        """
        connector = self.env['auto.monitoring.db.connector']

        query = """
            SELECT
                id, imei, trip_date, route_description,
                in_city_km, outside_city_km, total_km,
                city_coefficient, outside_coefficient, fuel_liters,
                project_name, payment_type, driver_name,
                trip_purpose_id, trip_purpose_other, user_comment,
                start_time, end_time, start_address, end_address,
                processed_at, updated_at
            FROM tracker_trips
            ORDER BY trip_date DESC, id DESC
        """

        rows = connector.execute_query(query)
        if not rows:
            _logger.warning("No trips found in external DB")
            return 0

        synced = 0
        now = fields.Datetime.now()

        for row in rows:
            vals = {
                'external_id': row.get('id'),
                'imei': row.get('imei') or '',
                'trip_date': row.get('trip_date'),
                'route_description': row.get('route_description') or '',
                'in_city_km': row.get('in_city_km') or 0,
                'outside_city_km': row.get('outside_city_km') or 0,
                'total_km': row.get('total_km') or 0,
                'city_coefficient': row.get('city_coefficient') or 0.0,
                'outside_coefficient': row.get('outside_coefficient') or 0.0,
                'fuel_liters': row.get('fuel_liters') or 0.0,
                'project_name': row.get('project_name') or '',
                'payment_type': row.get('payment_type') or '',
                'driver_name': row.get('driver_name') or '',
                'trip_purpose_other': row.get('trip_purpose_other') or '',
                'user_comment': row.get('user_comment') or '',
                'start_time': row.get('start_time'),
                'end_time': row.get('end_time'),
                'start_address': row.get('start_address') or '',
                'end_address': row.get('end_address') or '',
                'processed_at': row.get('processed_at'),
                'updated_at': row.get('updated_at'),
                'last_sync': now,
            }

            # Handle trip_purpose_id - find by external_id
            ext_purpose_id = row.get('trip_purpose_id')
            if ext_purpose_id:
                purpose = self.env['auto.monitoring.trip.purpose'].search(
                    [('external_id', '=', ext_purpose_id)], limit=1
                )
                vals['trip_purpose_id'] = purpose.id if purpose else False
            else:
                vals['trip_purpose_id'] = False

            # Find existing record by external_id
            existing = self.search(
                [('external_id', '=', row.get('id'))], limit=1
            )

            if existing:
                # Update only sync fields, preserve user edits
                sync_vals = {k: v for k, v in vals.items()
                           if k not in ('trip_purpose_id', 'trip_purpose_other',
                                       'user_comment')}
                existing.with_context(sync_mode=True).write(sync_vals)
            else:
                self.with_context(sync_mode=True).create(vals)

            synced += 1

        _logger.info("Synced %d trips from external DB", synced)
        return synced

    def action_sync_trips(self):
        """Action to sync trips from external DB."""
        synced = self.sync_from_external_db()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('Synced %d trips from external database.') % synced,
                'type': 'success',
                'sticky': False,
            }
        }
