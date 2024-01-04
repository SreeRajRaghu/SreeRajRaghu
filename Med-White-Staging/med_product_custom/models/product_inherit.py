from odoo import models, fields, api


class NotifyTriggersInherit(models.Model):
    _inherit = "product.product"

    is_brokerage = fields.Boolean('Is Brokerage')
    unit_ids = fields.One2many('product.unit', 'product_id', string='Unit', required=True)


class ProductUnit(models.Model):
    _name = 'product.unit'

    name = fields.Char('Label')
    product_id = fields.Many2one('product.product')
