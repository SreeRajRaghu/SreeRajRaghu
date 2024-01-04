from odoo import models, fields, api


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals_list):
        unit_val = None
        if vals_list.get('invoice_line_ids'):
            unit_val = {str(ind):  n[2].get('product_unit_ids') for ind, n in enumerate(vals_list.get('invoice_line_ids'))
                        if n and n[2].get('product_unit_ids')}
        res = super(AccountMoveInherit, self).create(vals_list)
        if unit_val and not res.invoice_line_ids.product_unit_ids:
            for ind, line in enumerate(res.invoice_line_ids):
                line.product_unit_ids = unit_val[str(ind)]
        return res


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    is_brokerage = fields.Boolean(related="product_id.is_brokerage")
    product_id = fields.Many2one('product.product', string='Product')
    product_unit_ids = fields.Many2many('product.unit', string='Units')

    @api.onchange('product_id', 'product_unit_ids')
    def onchange_product_id(self):
        if self.product_id and self.product_id.unit_ids.ids:
            domain = [('id', 'in', self.product_id.unit_ids.ids)]
            return {'domain': {'product_unit_ids': domain}}
