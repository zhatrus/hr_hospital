import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AutoMonitoringTripPurpose(models.Model):
    """Trip Purpose model - dictionary of trip purposes from external DB.

    Read-only model that fetches data from external 'trip_purposes' table.
    """
    _name = 'auto.monitoring.trip.purpose'
    _description = 'Trip Purpose'
    _order = 'sort_order, name_uk'

    external_id = fields.Integer(
        string='External ID',
        readonly=True,
        index=True,
        help='ID from external trip_purposes table',
    )
    code = fields.Char(
        string='Code',
        size=50,
        readonly=True,
        index=True,
        help='Unique code (meeting, training, etc.)',
    )
    name_uk = fields.Char(
        string='Name',
        size=255,
        required=True,
        help='Ukrainian name for display',
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the purpose',
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this purpose is available for selection',
    )
    sort_order = fields.Integer(
        string='Sort Order',
        default=0,
        help='Order for display in selection lists',
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Code must be unique!'),
    ]

    @api.model
    def sync_from_external_db(self):
        """Sync trip purposes from external database."""
        connector = self.env['auto.monitoring.db.connector']

        query = """
            SELECT id, code, name_uk, description, is_active, sort_order
            FROM trip_purposes
            WHERE is_active = true
            ORDER BY sort_order, name_uk
        """

        rows = connector.execute_query(query)
        if not rows:
            _logger.warning(
                "No trip purposes found in external DB or connection error"
            )
            return

        synced = 0
        for row in rows:
            vals = {
                'external_id': row.get('id'),
                'code': row.get('code'),
                'name_uk': row.get('name_uk'),
                'description': row.get('description'),
                'is_active': row.get('is_active', True),
                'sort_order': row.get('sort_order', 0),
            }

            existing = self.search(
                [('external_id', '=', row.get('id'))], limit=1
            )
            if existing:
                existing.write(vals)
            else:
                self.create(vals)
            synced += 1

        _logger.info("Synced %d trip purposes from external DB", synced)
        return synced

    def name_get(self):
        """Display name_uk as the name."""
        result = []
        for rec in self:
            result.append((rec.id, rec.name_uk))
        return result
