from odoo import fields, api, models
from odoo.exceptions import ValidationError


class medcellAssetMovement(models.Model):
    _name = 'asset.movement'
    _rec_name = 'product_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asset Movement'

    product_id = fields.Many2one('asset.product', string="Product Name")
    pro_category = fields.Many2one('medcell.product.category', string='Category')
    pro_sub_category = fields.Many2one('medcell.product.sub.category', string='Sub Category')
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    from_building = fields.Many2one('medcell.asset.building', string='Building')
    from_block = fields.Many2one('medcell.asset.block', string='Block')
    from_floor = fields.Many2one('medcell.asset.floor', string='Floor')
    from_room = fields.Many2one('medcell.asset.product.room', string='Room')
    from_company_id = fields.Many2one('res.company', string="From Which Institution")
    state = fields.Selection([('d', 'Draft'), ('c', 'Confirm')], string='State', default='d')
    user_building = fields.Many2one('medcell.asset.building', string="Building")
    user_floor = fields.Many2one('medcell.asset.floor', string='Floor')
    user_block = fields.Many2one('medcell.asset.block', string="Block")
    user_room = fields.Many2one('medcell.asset.product.room', string="Room")
    to_company_id = fields.Many2one('res.company', string="To Which Institution")
    date = fields.Date(string="Date")
    is_issue = fields.Boolean(string="Asset Issue")
    is_return = fields.Boolean(string="Asset Return")

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_asset_movement_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellAssetMovement, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_asset_movement_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellAssetMovement, self).unlink()


class Partner(models.Model):
    _inherit = 'res.partner'

    supplier = fields.Boolean('Is Supplier')
