from odoo import fields, models


class StockPickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'

    journal_id = fields.Many2one('account.journal', 'Journal')
