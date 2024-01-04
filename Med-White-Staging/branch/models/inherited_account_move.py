# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare




class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMove, self).default_get(default_fields)
        branch_id = False
        if self._context.get('branch_id'):
            branch_id = self._context.get('branch_id')
        elif self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id
        res.update({
            'branch_id': branch_id
        })
        return res

    branch_id = fields.Many2one('res.branch', string="Branch", default=lambda self: self.env.user.branch_id.id)
    branch_name = fields.Char(string='Branch Name')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMoveLine, self).default_get(default_fields)
        branch_id = False
        if self._context.get('branch_id'):
            branch_id = self._context.get('branch_id')
        elif self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id
        res.update({'branch_id': branch_id})
        return res

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.analytic_account_id = False
        if self.branch_id.analytic_account_id:
            self.analytic_account_id = self.branch_id.analytic_account_id.id

    branch_id = fields.Many2one('res.branch', string="Branch", store=True, readonly=False, default=lambda self: self.env.user.branch_id.id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True, related='branch_id.analytic_account_id')
    account_analytic_tag_id = fields.Many2one(comodel_name="account.analytic.tag", string="Analytic Tag", required=False, )
    branch_name_temp = fields.Char(string='Branch Name')
    branch_name = fields.Char(string='Branch Name')


    def _update_account_tag_aml(self):
        self._cr.execute('''update account_move_line aml set account_analytic_tag_id = rel_id.account_analytic_tag_id 
                            from account_analytic_tag_account_move_line_rel rel_id where aml.id = rel_id.account_move_line_id'''
                         )
    def _update_branch_name_aml(self):
        self._cr.execute('''update account_move_line aml set branch_name_temp = rb.name 
                                   from res_branch rb where aml.account_analytic_tag_id = rb.analytic_account_tag_id'''
                         )
    def _update_branch_id_aml(self):
        self._cr.execute('''update account_move_line aml set branch_id = rb.id 
                                           from res_branch rb where aml.account_analytic_tag_id = rb.analytic_account_tag_id'''
                         )

    def _update_branch_aml(self):
        self._cr.execute('''update account_move_line aml set branch_name = rb.name 
                                   from res_branch rb where aml.account_analytic_tag_id = rb.analytic_account_tag_id'''
                         )
    def _update_branch_null_aml(self):
        self._cr.execute('''update account_move_line aml set branch_name = '' where branch_name is null'''
                         )


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    branch_id = fields.Many2one('res.branch', string="Branch")
    branch_ids = fields.One2many('res.branch','analytic_account_id', string="Branches")
