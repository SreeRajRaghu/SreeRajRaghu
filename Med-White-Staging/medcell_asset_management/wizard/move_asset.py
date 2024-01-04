from odoo import api, fields, models
from odoo.exceptions import Warning, UserError, ValidationError


class AssetMove(models.TransientModel):
    _name = 'asset.move'

    @api.onchange('building_id')
    def onchange_building(self):
        blocks = []
        for block in self.building_id.block_line_ids:
            blocks.append(block.block_id.id)
        return {'domain': {'block_id': [('id', 'in', blocks)]}}

    @api.onchange('block_id')
    def onchange_block(self):
        floors = []
        for floor in self.block_id.floor_line_ids:
            floors.append(floor.floor_id.id)
        return {'domain': {'floor_id': [('id', 'in', floors)]}}

    @api.onchange('floor_id')
    def onchange_floor(self):
        rooms = []
        for room in self.env['medcell.asset.product.room'].search([('floor_id', '=', self.floor_id.id)]):
            rooms.append(room.id)
        return {'domain': {'room_id': [('id', 'in', rooms)]}}

    product_ids = fields.Many2many('asset.product', 'product_id', 'room_id', string='Product')
    return_product_ids = fields.Many2many('asset.product', string='Products')
    asset_move_id = fields.Many2one('asset.movement', string='Asset Movement')
    state = fields.Selection([('d', 'Draft'), ('c', 'Confirm')], string='State', default='d')
    date = fields.Date(string="Date", default=fields.Date.today)

    company_id = fields.Many2one('res.company', string="To Which Company",
                                 default=lambda self: self.env.user.company_id.id)
    building_id = fields.Many2one('medcell.asset.building', string="Building")
    block_id = fields.Many2one('medcell.asset.block', string="Block")
    floor_id = fields.Many2one('medcell.asset.floor', string='Floor')
    room_id = fields.Many2one('medcell.asset.product.room', string="Room")
    is_issue = fields.Boolean(string="Asset Issue")
    is_return = fields.Boolean(string="Asset Return")

    def confirm_move(self):
        products = []
        if self.product_ids:
            for product in self.product_ids:
                product.write({
                    'company_id': self.company_id.id,
                    'building_id': self.building_id.id,
                    'block_id': self.block_id.id,
                    'floor_id': self.floor_id.id,
                    'room_id': self.room_id.id,
                    'state': 'issued'
                })
                self.env['asset.movement'].create({
                    'date': self.date,
                    'is_issue': True,
                    'product_id': product.id,
                    'pro_category': product.product_category.id,
                    'pro_sub_category': product.product_sub_category.id,
                    'to_company_id': self.company_id.id,
                    'user_building': self.building_id.id,
                    'user_block': self.block_id.id,
                    'user_floor': self.floor_id.id,
                    'user_room': self.room_id.id,
                })
                products.append((0, 0, {
                    'product_id': product.id,
                }))
            self.room_id.asset_product_ids = products

    def action_asset_return(self):
        if self.return_product_ids:
            for product in self.return_product_ids:
                asset_product = self.env['asset.product.details'].search([('product_id', '=', product.id)])
                self.env['asset.movement'].create({
                    'date': self.date,
                    'is_return': True,
                    'product_id': product.id,
                    'pro_category': product.product_category.id,
                    'pro_sub_category': product.product_sub_category.id,
                    'from_company_id': asset_product.room_id.company_id.id,
                    'from_building': asset_product.room_id.building_id.id,
                    'from_block': asset_product.room_id.block_id.id,
                    'from_floor': asset_product.room_id.floor_id.id,
                    'from_room': asset_product.room_id.id
                })
                asset_product.unlink()
                product.write({
                    'company_id': None,
                    'building_id': None,
                    'block_id': None,
                    'floor_id': None,
                    'room_id': None,
                    'state': 'issued'
                })
                product.state = 'instock'
