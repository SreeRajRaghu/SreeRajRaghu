from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_discount_amount = fields.Monetary('Payment Discount')
    payment_amount = fields.Monetary(string='Payment Amount')
    is_discount = fields.Boolean('Is Discount')

    @api.depends(
        'invoice_line_ids', 'invoice_line_ids.price_subtotal', 'invoice_line_ids.discount',
        'invoice_line_ids.discount_fixed', 'is_discount', 'payment_discount_amount')
    def _compute_total_discount(self):
        for rec in self:
            tot_disc = 0
            for line in rec.invoice_line_ids:
                disc = (line.price_unit * line.quantity) - line.price_subtotal
                if self.discount_amount:
                    tot_disc += disc + self.payment_discount_amount
                else:
                    tot_disc += disc
            rec.total_discount = tot_disc
            rec.amount_total_gross = rec.amount_total + tot_disc
