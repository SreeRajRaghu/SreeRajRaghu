from odoo import models, fields, api


class medcellAssetManagement(models.Model):
    _name = 'medcell.asset.management'
    _description = 'medcell Asset Management'
    _rec_name = 'product_name'

    name = fields.Many2one('asset.product', string='Product Name')
    product_code = fields.Char(string='Product Code')
    category = fields.Many2one('medcell.product.category', string='Product Category')
    sub_category = fields.Many2one('medcell.product.sub.category', string='Product Sub Category')
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    active = fields.Boolean(string="Active", default=True)
    product_status = fields.Selection([("new", "New"), ("active", "Active"), ("damaged", "Damaged")],
                                      string='Product Status', default='active')
    sequence = fields.Char(string="Code", readonly=True, copy=False)
    sequencing_digit = fields.Char(string='Sequence Digit')
    purchase_date = fields.Date(string='Asset Date')
    room_id = fields.Many2one('medcell.asset.product.room', string='Room')
    building = fields.Char(string='Building', readonly=True)
    block = fields.Char(string='Block', readonly=True)
    floor = fields.Char(string='Floor', readonly=True)
    room = fields.Char(string='Room', readonly=True)
    category_name = fields.Char(string='Category Name')
    sub_category_name = fields.Char(string="Sub Category Name")
    asset_number = fields.Char(string='Asset Number')
    is_usertype = fields.Boolean(string='user type', compute='_get_usertype')
    product_name = fields.Char(string="Product Name")

    def _get_usertype(self):
        if not self.user_has_groups("medcell_asset_management.group_asset_manager"):
            self.is_usertype = True
        else:
            self.is_usertype = False
