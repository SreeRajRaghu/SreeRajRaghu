# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    barcode = fields.Char('Barcode', related="product_id.barcode")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    barcode = fields.Char('Barcode', related="product_id.barcode")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    barcode = fields.Char('Barcode', related="product_id.barcode")
