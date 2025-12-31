from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    """Extend Settings to add Fleet Monitoring configuration."""
    _inherit = 'res.config.settings'

    auto_monitoring_db_host = fields.Char(
        string='Host',
        config_parameter='auto_monitoring.db_host',
        default='localhost',
    )
    auto_monitoring_db_port = fields.Integer(
        string='Port',
        config_parameter='auto_monitoring.db_port',
        default=5432,
    )
    auto_monitoring_db_name = fields.Char(
        string='Database',
        config_parameter='auto_monitoring.db_name',
        default='monitoring',
    )
    auto_monitoring_db_user = fields.Char(
        string='User',
        config_parameter='auto_monitoring.db_user',
        default='lynx',
    )
    auto_monitoring_db_password = fields.Char(
        string='Password',
        config_parameter='auto_monitoring.db_password',
    )
    auto_monitoring_speed_limit = fields.Integer(
        string='Speed Limit (km/h)',
        config_parameter='auto_monitoring.speed_limit',
        default=130,
    )

    def action_test_db_connection(self):
        """Test the connection to external database."""
        self.ensure_one()

        self.env['ir.config_parameter'].sudo().set_param(
            'auto_monitoring.db_host', self.auto_monitoring_db_host or 'localhost')
        self.env['ir.config_parameter'].sudo().set_param(
            'auto_monitoring.db_port', str(self.auto_monitoring_db_port or 5432))
        self.env['ir.config_parameter'].sudo().set_param(
            'auto_monitoring.db_name', self.auto_monitoring_db_name or 'monitoring')
        self.env['ir.config_parameter'].sudo().set_param(
            'auto_monitoring.db_user', self.auto_monitoring_db_user or 'lynx')
        self.env['ir.config_parameter'].sudo().set_param(
            'auto_monitoring.db_password', self.auto_monitoring_db_password or '')

        connector = self.env['auto.monitoring.db.connector']
        connector.reset_connection_pool()

        success, message = connector.test_connection()

        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Успіх'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Помилка'),
                    'message': message,
                    'type': 'danger',
                    'sticky': True,
                }
            }
