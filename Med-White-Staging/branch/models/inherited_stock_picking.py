# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        account_move = self.move_lines.account_move_ids
        if account_move.mapped('line_ids'):
            lines = account_move.mapped('line_ids')
        else:
            lines = account_move.mapped('invoice_line_ids')
        [line.update({'branch_id': account_move.branch_id.id}) for line in lines]
        return res

    @api.model
    def default_get(self, default_fields):
        res = super(StockPicking, self).default_get(default_fields)
        if self.env.user.branch_id:
            res.update({
                'branch_id' : self.env.user.branch_id.id or False
            })
        return res

    branch_id = fields.Many2one('res.branch', string="Branch")