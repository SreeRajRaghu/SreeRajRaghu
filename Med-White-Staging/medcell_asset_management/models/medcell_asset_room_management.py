# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class medcellHostelRoom(models.Model):
    _name = 'medcell.asset.product.room'
    _description = 'medcell  Room'

    name = fields.Char(string='Cabin Number')
    room_name = fields.Char(string='Cabin Name')
    building_id = fields.Many2one('medcell.asset.building', string='Building', required=True)
    block_id = fields.Many2one('medcell.asset.block', string='Block', required=True)
    floor_id = fields.Many2one('medcell.asset.floor', string='Floor', required=True)
    facility_ids = fields.Many2many('medcell.asset.facility', string='Facilities')
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    product_ids = fields.One2many('asset.product', 'room_id', string="Products")
    asset_product_ids = fields.One2many('asset.product.details', 'room_id')
    responsible_person = fields.Many2one('hr.employee', string="Responsible Person")

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_cabin_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellHostelRoom, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_cabin_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellHostelRoom, self).unlink()

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

    # def _get_product_details(self):
    #     for pro in self.asset_product_ids:
    #         product_det = self.env['medcell.asset.management'].search([('name', '=', pro.product_id.id)])
    #         if not product_det:
    #             self.env['medcell.asset.management'].create({
    #                 'product_name': pro.product_name,
    #                 'category_name': pro.product_category.cat_name,
    #                 'sub_category_name': pro.product_sub_category.sub_cat_name,
    #                 'product_code': pro.product_code,
    #                 'building': self.building_id.name,
    #                 'block': self.block_id.name,
    #                 'floor': self.floor_id.name,
    #                 'room': self.name,
    #             })


class medcellFacility(models.Model):
    _name = 'medcell.asset.facility'
    _description = 'Add Facilities'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    # hostel_room_id = fields.Many2one('medcell.asset.product.room', 'Product Room')
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_asset_facilities_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellFacility, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_asset_facilities_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellFacility, self).unlink()


class medcellAssetProductDetails(models.Model):
    _name = 'asset.product.details'

    product_id = fields.Many2one('asset.product', string="Product")
    product_name = fields.Char(string="Product Name", related="product_id.asset_name")
    product_category = fields.Many2one('medcell.product.category', string='Product Category',
                                       related="product_id.product_category")
    product_sub_category = fields.Many2one('medcell.product.sub.category', string='Product Sub Category',
                                           related="product_id.product_sub_category")
    product_code = fields.Char(string=' Asset Code', related="product_id.product_code")
    room_id = fields.Many2one('medcell.asset.product.room', string="Room")
