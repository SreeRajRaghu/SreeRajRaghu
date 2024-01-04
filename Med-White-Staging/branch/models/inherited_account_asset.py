from odoo import api, fields, models, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    branch_id = fields.Many2one('res.branch', string="Branch")

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.account_analytic_id = False
        if self.branch_id.analytic_account_id:
            self.account_analytic_id = self.branch_id.analytic_account_id


class AssetModify(models.TransientModel):
    _name = 'asset.modify'

    branch_id = fields.Many2one('res.branch', string="Branch")
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account", required=False, )

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.analytic_account_id = False
        if self.branch_id.analytic_account_id:
            self.analytic_account_id = self.branch_id.analytic_account_id
