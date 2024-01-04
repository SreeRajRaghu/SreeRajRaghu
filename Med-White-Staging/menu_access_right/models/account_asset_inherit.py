from odoo import models, api


class AccountMoveInherit(models.Model):
    _inherit = 'account.asset'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """ Verifies that the operation given by ``operation`` is allowed for
            the current user according to the access rights.
        """
        if operation in ['write', 'create'] and not self.env.user.user_has_groups('menu_access_right.menu_asset_create_record'):
            return False
        return self.env['ir.model.access'].check(self._name, operation, raise_exception)