
from odoo import api, models, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains('default_code')
    def _check_unique_default_code(self):
        for product in self:
            if product.default_code:
                products = self.env['product.product'].search([
                    ('default_code', '=', product.default_code), ('id', '!=', product.id)
                ], limit=1)
                if products:
                    raise UserError(_('Internal Reference must be unique for every Product!'))
