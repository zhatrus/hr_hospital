import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AutoMonitoringTrip(models.Model):
    """Trip model - trips from external tracker_trips table.

    Model that fetches data from external 'tracker_trips' table.
    Users can edit trip_purpose_id and user_comment fields.
    Data is stored in external DB, not in Odoo.
    """
    _name = 'auto.monitoring.trip'
    _description = 'Trip'
    _order = 'trip_date desc, id desc'
    _auto = False  # Don't create table in Odoo DB

    id = fields.Integer(readonly=True)
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
        store=False,
    )
    imei = fields.Char(
        string='IMEI',
        size=20,
        readonly=True,
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
        store=False,
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
        store=False,
    )

    # Project
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

    # EDITABLE FIELDS
    trip_purpose_id = fields.Many2one(
        comodel_name='auto.monitoring.trip.purpose',
        string='Trip Purpose',
        help='Select trip purpose from list',
    )
    trip_purpose_other = fields.Text(
        string='Other Purpose',
        help='Specify if "Other" is selected',
    )
    user_comment = fields.Text(
        string='User Comment',
        help='Additional comments about the trip',
    )

    # Computed/Status fields
    is_editable = fields.Boolean(
        string='Editable',
        compute='_compute_is_editable',
        store=False,
        help='Can be edited until deadline',
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('completed', 'Completed'),
        ],
        default='completed',
        readonly=True,
    )

    processed_at = fields.Datetime(
        string='Processed At',
        readonly=True,
    )
    updated_at = fields.Datetime(
        string='Updated At',
        readonly=True,
    )

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

    @api.depends('total_km')
    def _compute_distance(self):
        """Convert total_km to float distance."""
        for rec in self:
            rec.distance = float(rec.total_km) if rec.total_km else 0.0

    @api.depends('fuel_liters')
    def _compute_fuel_consumed(self):
        """Alias for fuel_liters."""
        for rec in self:
            rec.fuel_consumed = rec.fuel_liters or 0.0

    @api.depends('trip_date')
    def _compute_is_editable(self):
        """Check if trip can be edited based on deadline.

        Deadline: end of trip month + 5 days of next month.
        After deadline, only manager/admin can edit.
        """
        for rec in self:
            if not rec.trip_date:
                rec.is_editable = False
                continue

            # Calculate deadline
            from dateutil.relativedelta import relativedelta
            deadline = rec.trip_date.replace(
                day=1
            ) + relativedelta(months=1, days=5)

            today = fields.Date.today()
            rec.is_editable = today <= deadline

    @api.model
    def _fetch_trips_data(self, domain=None, limit=100, offset=0):
        """Fetch trips from external tracker_trips table.

        Args:
            domain: List of filter conditions
            limit: Max number of records
            offset: Offset for pagination

        Returns:
            List of trip data dicts
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
                elif field == 'vehicle_id' and operator == '=':
                    # Get vehicle IMEI
                    vehicle = self.env['auto.monitoring.vehicle'].browse(value)
                    if vehicle and vehicle.imei:
                        where_clauses.append("imei = %s")
                        params.append(vehicle.imei)
                elif field == 'trip_date' and operator == '=':
                    where_clauses.append("trip_date = %s")
                    params.append(value)
                elif field == 'trip_date' and operator == '>=':
                    where_clauses.append("trip_date >= %s")
                    params.append(value)
                elif field == 'trip_date' and operator == '<=':
                    where_clauses.append("trip_date <= %s")
                    params.append(value)

        query = f"""
            SELECT
                id, imei, trip_date, route_description,
                in_city_km, outside_city_km, total_km,
                city_coefficient, outside_coefficient, fuel_liters,
                project_name, payment_type, driver_name,
                trip_purpose_id, trip_purpose_other, user_comment,
                is_editable, start_time, end_time,
                start_address, end_address,
                processed_at, updated_at
            FROM tracker_trips
            WHERE {' AND '.join(where_clauses)}
            ORDER BY trip_date DESC, id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        return connector.execute_query(query, tuple(params))

    @api.model
    def search(self, domain=None, offset=0, limit=None, order=None):
        """Override search to return IDs from external DB."""
        data = self._fetch_trips_data(domain, limit or 100, offset)
        return [row.get('id') for row in data]

    def read(self, fields=None, load='_classic_read'):
        """Override read to fetch from external DB."""
        if isinstance(self.ids, (list, tuple)) and self.ids:
            ids = self.ids
        else:
            ids = [self.id] if self.id else []

        if not ids:
            return []

        connector = self.env['auto.monitoring.db.connector']
        query = """
            SELECT
                id, imei, trip_date, route_description,
                in_city_km, outside_city_km, total_km,
                city_coefficient, outside_coefficient, fuel_liters,
                project_name, payment_type, driver_name,
                trip_purpose_id, trip_purpose_other, user_comment,
                is_editable, start_time, end_time,
                start_address, end_address,
                processed_at, updated_at
            FROM tracker_trips
            WHERE id = ANY(%s)
        """
        data = connector.execute_query(query, (ids,))

        if fields:
            return [
                {k: v for k, v in row.items() if k in fields or k == 'id'}
                for row in data
            ]
        return data

    @api.model
    def search_read(self, domain=None, fields=None, offset=0,
                    limit=None, order=None):
        """Override to fetch data from external DB."""
        limit = limit or 100
        data = self._fetch_trips_data(domain, limit, offset)

        if fields:
            return [
                {k: v for k, v in row.items() if k in fields or k == 'id'}
                for row in data
            ]
        return data

    def write(self, vals):
        """Override write to update external DB.

        Only trip_purpose_id, trip_purpose_other, and user_comment
        can be updated by users.
        """
        self.ensure_one()

        # Check if user can edit
        is_manager = self.env.user.has_group(
            'auto_monitoring.group_auto_monitoring_manager'
        )

        if not is_manager and not self.is_editable:
            raise UserError(_(
                'This trip cannot be edited. '
                'Deadline has passed (end of month + 5 days).'
            ))

        # Only allow editing specific fields
        allowed_fields = {
            'trip_purpose_id', 'trip_purpose_other', 'user_comment'
        }
        if not is_manager:
            invalid_fields = set(vals.keys()) - allowed_fields
            if invalid_fields:
                raise UserError(_(
                    'You can only edit: Trip Purpose and User Comment'
                ))

        connector = self.env['auto.monitoring.db.connector']

        # Prepare update query
        update_parts = []
        params = []

        if 'trip_purpose_id' in vals:
            update_parts.append("trip_purpose_id = %s")
            params.append(vals['trip_purpose_id'])

        if 'trip_purpose_other' in vals:
            update_parts.append("trip_purpose_other = %s")
            params.append(vals['trip_purpose_other'])

        if 'user_comment' in vals:
            update_parts.append("user_comment = %s")
            params.append(vals['user_comment'])

        if not update_parts:
            return True

        update_parts.append("updated_at = CURRENT_TIMESTAMP")
        params.append(self.id)

        query = f"""
            UPDATE tracker_trips
            SET {', '.join(update_parts)}
            WHERE id = %s
        """

        connector.execute_query(query, tuple(params), fetchall=False)

        return True
