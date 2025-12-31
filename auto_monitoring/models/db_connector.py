import logging
from contextlib import contextmanager

from odoo import api, models, tools

_logger = logging.getLogger(__name__)

try:
    import psycopg2
except ImportError:
    psycopg2 = None
    _logger.warning("psycopg2 not installed. External DB features won't work.")


class AutoMonitoringDBConnector(models.AbstractModel):
    """Abstract model for connecting to external PostgreSQL database.

    Provides connection pooling and helper methods for executing queries
    against the external monitoring database.
    """
    _name = 'auto.monitoring.db.connector'
    _description = 'External DB Connector'

    _connection_pool = None

    @api.model
    def _get_db_config(self):
        """Get database connection parameters from system parameters or config."""
        ICP = self.env['ir.config_parameter'].sudo()

        config = {
            'host': ICP.get_param('auto_monitoring.db_host', 'localhost'),
            'port': int(ICP.get_param('auto_monitoring.db_port', '5432')),
            'database': ICP.get_param('auto_monitoring.db_name', 'monitoring'),
            'user': ICP.get_param('auto_monitoring.db_user', 'lynx'),
            'password': ICP.get_param('auto_monitoring.db_password', ''),
        }

        odoo_config = tools.config
        if odoo_config.get('auto_monitoring_db_host'):
            config['host'] = odoo_config.get('auto_monitoring_db_host')
        if odoo_config.get('auto_monitoring_db_port'):
            config['port'] = int(odoo_config.get('auto_monitoring_db_port'))
        if odoo_config.get('auto_monitoring_db_name'):
            config['database'] = odoo_config.get('auto_monitoring_db_name')
        if odoo_config.get('auto_monitoring_db_user'):
            config['user'] = odoo_config.get('auto_monitoring_db_user')
        if odoo_config.get('auto_monitoring_db_password'):
            config['password'] = odoo_config.get('auto_monitoring_db_password')

        return config

    @api.model
    def _get_connection_pool(self):
        """Get or create connection pool for external database."""
        if not psycopg2:
            _logger.error("psycopg2 is not installed")
            return None

        if AutoMonitoringDBConnector._connection_pool is None:
            try:
                config = self._get_db_config()
                AutoMonitoringDBConnector._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=config['host'],
                    port=config['port'],
                    database=config['database'],
                    user=config['user'],
                    password=config['password'],
                )
                _logger.info(
                    "Created pool for external DB: %s@%s:%s/%s",
                    config['user'], config['host'],
                    config['port'], config['database'])
            except Exception as e:
                _logger.error("Failed to create connection pool: %s", e)
                return None
        return AutoMonitoringDBConnector._connection_pool

    @contextmanager
    def _get_connection(self):
        """Context manager for getting a connection from the pool."""
        pool_obj = self._get_connection_pool()
        if pool_obj is None:
            yield None
            return

        conn = None
        try:
            conn = pool_obj.getconn()
            yield conn
        except Exception as e:
            _logger.error("Error getting connection: %s", e)
            yield None
        finally:
            if conn:
                pool_obj.putconn(conn)

    @api.model
    def execute_query(self, query, params=None, fetchall=True):
        """Execute a query on the external database.

        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetchall: If True, return all rows; if False, return one row

        Returns:
            List of dicts (fetchall=True) or single dict (fetchall=False) or None on error
        """
        with self._get_connection() as conn:
            if conn is None:
                _logger.warning("No connection available for query")
                return [] if fetchall else None

            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    cols = [d[0] for d in cur.description] if cur.description else []

                    if fetchall:
                        rows = cur.fetchall()
                        return [dict(zip(cols, row)) for row in rows]
                    else:
                        row = cur.fetchone()
                        return dict(zip(cols, row)) if row else None
            except Exception as e:
                _logger.error("Query execution error: %s\nQuery: %s", e, query)
                return [] if fetchall else None

    @api.model
    def test_connection(self):
        """Test the connection to the external database."""
        with self._get_connection() as conn:
            if conn is None:
                return False, "Не вдалося підключитися до бази даних"
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True, "Підключення успішне"
            except Exception as e:
                return False, f"Помилка: {e}"

    @api.model
    def reset_connection_pool(self):
        """Reset the connection pool (e.g., after config change)."""
        if AutoMonitoringDBConnector._connection_pool:
            try:
                AutoMonitoringDBConnector._connection_pool.closeall()
            except Exception as e:
                _logger.warning("Error closing connection pool: %s", e)
            AutoMonitoringDBConnector._connection_pool = None
        _logger.info("Connection pool reset")
