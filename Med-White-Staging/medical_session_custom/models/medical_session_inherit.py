from odoo import fields, models


class MedicalSessionInherit(models.Model):
    _inherit = 'medical.session'

    def _cron_close_daily_sessions(self):
        for rec in self.search([('state', '=', 'opened'),
                                ('config_id.disable_closing', '=', False)]):
            rec._session_validate()


class SessionConfigInherit(models.Model):
    _inherit = 'medical.config'

    disable_closing = fields.Boolean('Disable Closing')