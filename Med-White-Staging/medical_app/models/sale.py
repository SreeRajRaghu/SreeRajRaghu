# -*- coding: utf-8 -*-

from odoo import models


# class SaleAdvancePaymentInv(models.TransientModel):
#     _inherit = "sale.advance.payment.inv"

#     def _create_invoice(self, order, so_line, amount):
#         invoice = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
#         for line in invoice.invoice_line_ids:
#             line.account_analytic_id = self.product_id.analytic_account_id.id or self.product_id.categ_id.analytic_account_id.id
#         return invoice
