# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class medcellHostel(models.Model):
    _name = 'medcell.asset.building'
    _description = 'Create Building'

    name = fields.Char(string='Name', required=True)
    capacity = fields.Integer(compute='get_capacity', string='Building Capacity')
    # block_lines = fields.One2many('medcell.asset.block', 'building_id', string="Block")
    block_line_ids = fields.One2many('medcell.asset.block.line', 'building_id', string="Block")
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_buildings_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellHostel, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_buildings_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellHostel, self).unlink()

    def get_capacity(self):
        for rec in self:
            room_count = self.env['medcell.asset.product.room'].search_count([('building_id', '=', rec.id)])
            rec.capacity = room_count

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name must be unique !')
    ]


class medcellBuildingBlockLines(models.Model):
    _name = 'medcell.asset.block.line'

    block_id = fields.Many2one('medcell.asset.block', strng="Block")
    block_code = fields.Char(string="Code", related="block_id.code")
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 related="block_id.company_id")
    building_id = fields.Many2one('medcell.asset.building', string="Building")


class medcellAssetBlock(models.Model):
    _name = 'medcell.asset.block'
    _description = """medcell Block Details"""

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    building_id = fields.Many2one('medcell.asset.building', string="Building")
    floor_line_ids = fields.One2many('medcell.asset.floor.line', 'block_id', string="Floor")
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_block_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellAssetBlock, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_block_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellAssetBlock, self).unlink()

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name must be unique !')
    ]


class medcellBlockFloorLine(models.Model):
    _name = 'medcell.asset.floor.line'

    floor_id = fields.Many2one('medcell.asset.floor', string="Floor")
    floor_code = fields.Char('Code', related="floor_id.code")
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 related="floor_id.company_id")
    block_id = fields.Many2one('medcell.asset.block', string="Block")


class medcellAssetFloor(models.Model):
    _name = 'medcell.asset.floor'
    _description = """medcell Floor Details"""

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    block_id = fields.Many2one('medcell.asset.block', string="Block")
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_floor_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellAssetFloor, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_floor_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellAssetFloor, self).unlink()

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name must be unique !')
    ]


class AssetGlobalBuilding(models.Model):
    _name = 'global.asset.building'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    block_lines = fields.One2many('medcell.asset.block', 'building_id', string="Block")
    company_id = fields.Many2one('res.company', 'Institution', required=True)


class AssetGlobalBlock(models.Model):
    _name = 'global.asset.block'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    building_id = fields.Many2one('medcell.asset.building', string="Building")
    floor_lines = fields.One2many('medcell.asset.floor', 'block_id', string="Floor")
    company_id = fields.Many2one('res.company', 'Institution', required=True)


class AssetGlobalFloor(models.Model):
    _name = 'global.asset.floor'
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    block_id = fields.Many2one('medcell.asset.block', string="Block")

    company_id = fields.Many2one('res.company', 'Company', required=True)
