from odoo import models, fields


class GenerateBulkAssetsWizard(models.TransientModel):
    _name = 'generate.bulk.assets'

    name = fields.Char(string="Product Name")
    group_id = fields.Many2one('medcell.products.group', string="Group")
    category_id = fields.Many2one('medcell.product.category', string='Category',
                                  related="sub_category_id.product_category_id")
    sub_category_id = fields.Many2one('medcell.product.sub.category', string='Sub Category',
                                      related="group_id.product_sub_category_id")
    brand_id = fields.Many2one('medcell.asset.brand', string="Brand")
    purchase_date = fields.Date(string="Purchase Date")
    product_count = fields.Integer(string="Asset Count", required=True)

    def generate_bulk_products(self):
        if self.name and self.product_count:
            for i in list(range(self.product_count)):
                self.env['asset.product'].create({
                    'asset_name': self.name,
                    'group_id': self.group_id.id,
                    'brand_id': self.brand_id.id,
                    'purchase_date': self.purchase_date,
                    'sequence': str(i + 1)
                })
