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
        string='Is Editable',
        compute='_compute_is_editable',
        search='_search_is_editable',
        store=False,
        help='Can this trip be edited (deadline check)',
    )
    is_manager = fields.Boolean(
        string='Is Manager',
        compute='_compute_is_manager',
        store=False,
        help='Current user is manager or admin',
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

    def _compute_is_manager(self):
        """Check if current user is manager or admin."""
        is_manager = self.env.user.has_group(
            'auto_monitoring.group_auto_monitoring_manager'
        )
        for rec in self:
            rec.is_manager = is_manager

    def _search_is_editable(self, operator, value):
        """Search method for is_editable computed field.

        Returns domain that filters trips based on deadline.
        """
        from dateutil.relativedelta import relativedelta

        today = fields.Date.today()

        # Calculate the earliest date that is still editable
        # (end of previous month + 5 days)
        cutoff_date = today.replace(day=1) - relativedelta(days=5)

        if operator == '=' and value:
            # Return trips that are still editable (after cutoff)
            return [('trip_date', '>=', cutoff_date)]
        elif operator == '=' and not value:
            # Return trips that are not editable (before cutoff)
            return [('trip_date', '<', cutoff_date)]
        elif operator == '!=' and value:
            # Return trips that are not editable
            return [('trip_date', '<', cutoff_date)]
        elif operator == '!=' and not value:
            # Return trips that are editable
            return [('trip_date', '>=', cutoff_date)]
        else:
            return []

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

        data = connector.execute_query(query, tuple(params))

        # Convert None to False for Many2one and other fields
        # Odoo expects False instead of None for empty values
        many2one_fields = ['trip_purpose_id', 'vehicle_id']
        for row in data:
            for key, value in row.items():
                if value is None:
                    if key in many2one_fields:
                        row[key] = False
                    elif key in ['route_description', 'project_name',
                                 'payment_type', 'driver_name',
                                 'trip_purpose_other', 'user_comment',
                                 'start_address', 'end_address']:
                        row[key] = ''
                    else:
                        row[key] = False

        return data

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None,
                     order=None):
        """Override search_fetch to fetch data from external DB."""
        # Fetch data from external DB
        data = self._fetch_trips_data(domain, limit or 100, offset)

        # Create recordset with IDs
        ids = [row.get('id') for row in data]
        records = self.browse(ids)

        # Populate cache for all fields from external DB
        for row in data:
            record = self.browse([row['id']])
            for field_name, value in row.items():
                if field_name in self._fields:
                    record._cache[field_name] = value

        # Compute all computed fields that are requested
        if field_names:
            for field_name in field_names:
                if field_name in self._fields:
                    field = self._fields[field_name]
                    if field.compute and not field.store:
                        # Trigger compute for this field
                        records.mapped(field_name)

        return records

    @api.model
    def search(self, domain=None, offset=0, limit=None, order=None,
               count=False):
        """Override search to return recordset from external DB."""
        if count:
            data = self._fetch_trips_data(domain, limit or 100, offset)
            return len(data)

        # Fetch data and create recordset
        data = self._fetch_trips_data(domain, limit or 100, offset)
        ids = [row.get('id') for row in data]

        # Create recordset and populate cache
        records = self.browse(ids)
        for row in data:
            record = self.browse([row['id']])
            for field_name, value in row.items():
                if field_name in self._fields:
                    record._cache[field_name] = value

        return records

    def read(self, fields=None, load='_classic_read'):
        """Override read to fetch from external DB and compute fields."""
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

        # Convert None to False for Many2one and other fields
        many2one_fields = ['trip_purpose_id', 'vehicle_id']
        text_fields = ['route_description', 'project_name', 'payment_type',
                       'driver_name', 'trip_purpose_other', 'user_comment',
                       'start_address', 'end_address']
        for row in data:
            for key, value in row.items():
                if value is None:
                    if key in many2one_fields:
                        row[key] = False
                    elif key in text_fields:
                        row[key] = ''
                    else:
                        row[key] = False

        # Populate cache for records
        for row in data:
            record = self.browse([row['id']])
            for field_name, value in row.items():
                if field_name in self._fields:
                    record._cache[field_name] = value

        # Add computed fields to result
        result = []
        for row in data:
            record_data = dict(row)

            # Compute vehicle_id from imei
            if not fields or 'vehicle_id' in fields:
                imei = row.get('imei')
                if imei:
                    vehicle = self.env['auto.monitoring.vehicle'].search(
                        [('imei', '=', imei)], limit=1
                    )
                    record_data['vehicle_id'] = vehicle.id if vehicle else False
                else:
                    record_data['vehicle_id'] = False

            # Compute distance
            if not fields or 'distance' in fields:
                in_city = row.get('in_city_km') or 0
                outside = row.get('outside_city_km') or 0
                record_data['distance'] = in_city + outside

            # Compute fuel_consumed
            if not fields or 'fuel_consumed' in fields:
                record_data['fuel_consumed'] = row.get('fuel_liters') or 0.0

            # Compute is_manager
            if not fields or 'is_manager' in fields:
                record_data['is_manager'] = self.env.user.has_group(
                    'auto_monitoring.group_auto_monitoring_manager'
                )

            result.append(record_data)

        if fields:
            return [
                {k: v for k, v in row.items() if k in fields or k == 'id'}
                for row in result
            ]
        return result

    @api.model
    def search_read(self, domain=None, fields=None, offset=0,
                    limit=None, order=None):
        """Override to fetch data from external DB."""
        limit = limit or 100
        data = self._fetch_trips_data(domain, limit, offset)

        # Add computed fields to each row
        result = []
        for row in data:
            record_data = dict(row)

            # Compute vehicle_id from imei
            if not fields or 'vehicle_id' in fields:
                imei = row.get('imei')
                if imei:
                    vehicle = self.env['auto.monitoring.vehicle'].search(
                        [('imei', '=', imei)], limit=1
                    )
                    record_data['vehicle_id'] = vehicle.id if vehicle else False
                else:
                    record_data['vehicle_id'] = False

            # Compute distance
            if not fields or 'distance' in fields:
                in_city = row.get('in_city_km') or 0
                outside = row.get('outside_city_km') or 0
                record_data['distance'] = in_city + outside

            # Compute fuel_consumed
            if not fields or 'fuel_consumed' in fields:
                record_data['fuel_consumed'] = row.get('fuel_liters') or 0.0

            # Compute is_manager
            if not fields or 'is_manager' in fields:
                record_data['is_manager'] = self.env.user.has_group(
                    'auto_monitoring.group_auto_monitoring_manager'
                )

            result.append(record_data)

        if fields:
            return [
                {k: v for k, v in row.items() if k in fields or k == 'id'}
                for row in result
            ]
        return result

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        """Override read_group to work with external DB.

        This is needed for pivot and graph views.
        """
        connector = self.env['auto.monitoring.db.connector']

        # Parse groupby
        if not groupby:
            return []

        groupby_field = groupby[0].split(':')[0] if ':' in groupby[0] \
            else groupby[0]

        # Build aggregation query
        select_parts = [f'"{groupby_field}"']
        group_parts = [f'"{groupby_field}"']

        # Parse measure fields
        for field_spec in fields:
            if ':' in field_spec:
                field_name, agg = field_spec.split(':')
                if agg in ('sum', 'avg', 'count', 'min', 'max'):
                    select_parts.append(
                        f'{agg.upper()}("{field_name}") as "{field_name}"'
                    )
            else:
                # Default aggregation is count
                select_parts.append(f'COUNT(*) as "{field_spec}_count"')

        # Add __count for Odoo
        select_parts.append('COUNT(*) as "__count"')

        query = f"""
            SELECT {', '.join(select_parts)}
            FROM tracker_trips
            GROUP BY {', '.join(group_parts)}
            ORDER BY "{groupby_field}"
        """

        try:
            result = connector.execute_query(query, fetchall=True)

            # Format result for Odoo
            formatted_result = []
            for row in result:
                record = {
                    groupby_field: row.get(groupby_field),
                    '__domain': [(groupby_field, '=', row.get(groupby_field))],
                }

                # Add aggregated values
                for field_spec in fields:
                    if ':' in field_spec:
                        field_name = field_spec.split(':')[0]
                        record[field_name] = row.get(field_name, 0)
                    else:
                        record[f'{field_spec}_count'] = \
                            row.get(f'{field_spec}_count', 0)

                record['__count'] = row.get('__count', 0)
                formatted_result.append(record)

            return formatted_result

        except Exception as e:
            _logger.error(f"Error in read_group: {e}")
            return []

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
