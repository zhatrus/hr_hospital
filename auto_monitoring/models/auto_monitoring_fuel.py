import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AutoMonitoringFuelTransaction(models.Model):
    """Fuel Transaction model - refueling data from external DB.

    Fetches fuel card transactions from external 'fuel_transactions' table.
    """
    _name = 'auto.monitoring.fuel.transaction'
    _description = 'Fuel Transaction'
    _order = 'trans_date desc'
    _auto = False

    id = fields.Integer(readonly=True)
    trans_id = fields.Integer(
        string='Transaction ID',
        readonly=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name='auto.monitoring.vehicle',
        string='Vehicle',
        compute='_compute_vehicle_id',
        store=False,
    )
    card_num = fields.Char(
        string='Card Number',
        size=20,
        readonly=True,
    )
    card_num_masked = fields.Char(
        string='Card',
        compute='_compute_card_masked',
        store=False,
    )
    trans_date = fields.Datetime(
        string='Date',
        readonly=True,
    )
    volume = fields.Float(
        string='Volume (L)',
        digits=(10, 2),
        readonly=True,
    )
    price = fields.Float(
        string='Price (per L)',
        digits=(8, 2),
        readonly=True,
    )
    amount = fields.Float(
        string='Amount',
        digits=(12, 2),
        readonly=True,
    )
    azs_name = fields.Char(
        string='Gas Station',
        size=100,
        readonly=True,
    )
    address = fields.Char(
        string='Address',
        size=200,
        readonly=True,
    )
    product_desc = fields.Char(
        string='Fuel Type',
        size=100,
        readonly=True,
    )
    client_name = fields.Char(
        string='Client',
        size=100,
        readonly=True,
    )

    @api.depends('card_num')
    def _compute_card_masked(self):
        for rec in self:
            if rec.card_num and len(rec.card_num) >= 4:
                rec.card_num_masked = f"****{rec.card_num[-4:]}"
            else:
                rec.card_num_masked = rec.card_num or ''

    @api.depends('card_num')
    def _compute_vehicle_id(self):
        Vehicle = self.env['auto.monitoring.vehicle']
        for rec in self:
            if rec.card_num:
                vehicle = Vehicle.search(
                    [('fuel_card_number', '=', rec.card_num)], limit=1
                )
                rec.vehicle_id = vehicle.id if vehicle else False
            else:
                rec.vehicle_id = False

    @api.model
    def _fetch_fuel_data(self, domain=None, limit=100, offset=0):
        """Fetch fuel transactions from external database."""
        connector = self.env['auto.monitoring.db.connector']

        where_clauses = ["1=1"]
        params = []

        if domain:
            for condition in domain:
                field, operator, value = condition
                if field == 'card_num' and operator == '=':
                    where_clauses.append("card_num = %s")
                    params.append(value)
                elif field == 'trans_date' and operator == '>=':
                    where_clauses.append("trans_date >= %s")
                    params.append(value)
                elif field == 'trans_date' and operator == '<=':
                    where_clauses.append("trans_date <= %s")
                    params.append(value)

        query = f"""
            SELECT trans_id as id, trans_id, card_num, trans_date,
                   volume, price, amnt_trans as amount,
                   azs_name, addr_name as address, product_desc, client_name
            FROM fuel_transactions
            WHERE {' AND '.join(where_clauses)}
            ORDER BY trans_date DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        return connector.execute_query(query, tuple(params))

    @api.model
    def search_read(self, domain=None, fields=None, offset=0,
                    limit=None, order=None):
        """Override to fetch data from external DB."""
        limit = limit or 100
        data = self._fetch_fuel_data(domain, limit, offset)

        if fields:
            return [
                {k: v for k, v in row.items() if k in fields or k == 'id'}
                for row in data
            ]
        return data

    @api.model
    def get_monthly_stats(self, year=None, month=None):
        """Get monthly fuel statistics."""
        connector = self.env['auto.monitoring.db.connector']

        now = fields.Datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month

        query = """
            SELECT
                COUNT(*) as transaction_count,
                COALESCE(SUM(volume), 0) as total_volume,
                COALESCE(SUM(amnt_trans), 0) as total_amount,
                COALESCE(AVG(price), 0) as avg_price
            FROM fuel_transactions
            WHERE EXTRACT(YEAR FROM trans_date) = %s
              AND EXTRACT(MONTH FROM trans_date) = %s
        """

        result = connector.execute_query(query, (year, month), fetchall=False)
        return result or {
            'transaction_count': 0,
            'total_volume': 0,
            'total_amount': 0,
            'avg_price': 0,
        }

    @api.model
    def get_vehicle_consumption(self, vehicle_id, days=30):
        """Calculate fuel consumption for a vehicle."""
        vehicle = self.env['auto.monitoring.vehicle'].browse(vehicle_id)
        if not vehicle or not vehicle.fuel_card_number:
            return None

        connector = self.env['auto.monitoring.db.connector']
        since = fields.Datetime.now() - timedelta(days=days)

        query_fuel = """
            SELECT COALESCE(SUM(volume), 0) as total_fuel
            FROM fuel_transactions
            WHERE card_num = %s AND trans_date >= %s
        """
        fuel_result = connector.execute_query(
            query_fuel, (vehicle.fuel_card_number, since), fetchall=False
        )
        total_fuel = fuel_result.get('total_fuel', 0) if fuel_result else 0

        query_mileage = """
            SELECT
                (MAX(odometer) - MIN(odometer)) / 1000.0 as mileage
            FROM tracker_light
            WHERE imei = %s AND timestamp >= %s
        """
        mileage_result = connector.execute_query(
            query_mileage, (vehicle.imei, since), fetchall=False
        )
        mileage = mileage_result.get('mileage', 0) if mileage_result else 0

        consumption = (total_fuel / mileage * 100) if mileage > 0 else 0
        if vehicle.fuel_norm:
            deviation = (
                (consumption - vehicle.fuel_norm) / vehicle.fuel_norm * 100
            )
        else:
            deviation = 0

        return {
            'vehicle_id': vehicle.id,
            'vehicle_name': vehicle.display_name,
            'total_fuel': round(total_fuel, 2),
            'mileage': round(mileage, 1),
            'consumption': round(consumption, 2),
            'norm': vehicle.fuel_norm,
            'deviation': round(deviation, 1),
            'status': (
                'ok' if deviation <= 5
                else ('warning' if deviation <= 15 else 'danger')
            ),
        }
