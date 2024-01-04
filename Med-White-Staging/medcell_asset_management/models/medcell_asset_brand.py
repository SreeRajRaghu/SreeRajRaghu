from odoo import models, fields, api
from odoo.exceptions import Warning as UserError


class medcellAssetBrand(models.Model):
    _name = 'medcell.asset.brand'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_product_brand_create"):
            raise UserError("Sorry, you are not allowed to create a record.")
        return super(medcellAssetBrand, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_product_brand_delete"):
            raise UserError("Sorry, you are not allowed to delete the Record.")
        return super(medcellAssetBrand, self).unlink()


class AssetMoveReturn(models.Model):
    _name = 'asset.move.issue.details'
    _rec_name = 'product_id'

    product_id = fields.Many2one('asset.product', string="Product Name")
    handover_date = fields.Date(string="Handover Date")
    return_date = fields.Date(string="Return Date")
    employee_id = fields.Many2one('hr.employee', string="Employee")


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    asset_move_issue_ids = fields.One2many('asset.move.issue.details', 'employee_id', readonly=True)


class medcellProductsGroup(models.Model):
    _name = 'medcell.products.group'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    sequence = fields.Char(string="Sequence", readonly=True)
    product_sub_category_id = fields.Many2one('medcell.product.sub.category', string="Product Sub Category")
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        res = super(medcellProductsGroup, self).create(vals)
        if self.user_has_groups("medcell_asset_management.group_product_group_create"):
            if res.product_sub_category_id:
                vals1 = {
                    'name': res.name,
                    'code': res.code,
                    'active': 'true',
                    'prefix': res.product_sub_category_id.product_category_id.cat_code + '/'
                              + res.product_sub_category_id.sub_cat_code + '/' + res.code,
                    'number_increment': 1,
                    'padding': 4,
                    'number_next_actual': 1,
                    'implementation': 'standard',
                    'company_id': res.company_id.id
                }
                res.sequence = self.env['ir.sequence'].create(vals1).code
            else:
                raise UserError('Please Select Product Sub Category')
        else:
            raise UserError("Sorry, you are not allowed to create a record.")
        return res

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_product_group_delete"):
            raise UserError("Sorry, you are not allowed to delete the Record.")
        return super(medcellProductsGroup, self).unlink()
