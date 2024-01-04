from odoo import models, fields, api, _
from odoo.osv import expression
import qrcode
import base64
from odoo.exceptions import UserError, Warning, ValidationError
from io import BytesIO


class medcellProductCategory(models.Model):
    _name = 'medcell.product.category'
    _rec_name = 'cat_name'

    cat_name = fields.Char(string='Name', required=True)
    cat_code = fields.Char(string='Code', required=True)
    product_category_ids = fields.One2many('medcell.product.sub.category', 'product_category_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    sequence = fields.Char(string='Sequence')
    sequencing_digit = fields.Char(string='Sequence Digit')

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_product_category_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellProductCategory, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_product_category_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellProductCategory, self).unlink()

    _sql_constraints = [
        ('cat_name_uniq', 'unique (cat_name, company_id)', 'The Product Category must be unique !')]


class medcellProductSubCategory(models.Model):
    _name = 'medcell.product.sub.category'
    _rec_name = 'sub_cat_name'

    sub_cat_name = fields.Char(string='Name', required=True)
    sub_cat_code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    sequence = fields.Char(string='Sequence')
    sequencing_digit = fields.Integer(string='Sequence Digit')
    group_ids = fields.One2many('medcell.products.group', 'product_sub_category_id', string="Group", readonly=True)
    product_category_id = fields.Many2one('medcell.product.category', string="Product Category")

    @api.model
    def create(self, vals):
        if not self.user_has_groups("medcell_asset_management.group_product_sub_category_create"):
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return super(medcellProductSubCategory, self).create(vals)

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_product_sub_category_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellProductSubCategory, self).unlink()

    _sql_constraints = [
        ('sub_cat_name_uniq', 'unique (sub_cat_name, company_id)', 'The Product Category must be unique !')]


class medcellProduct(models.Model):
    _name = 'asset.product'
    _rec_name = 'product_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product'

    product_category = fields.Many2one('medcell.product.category', string='Product Category',
                                       related="product_sub_category.product_category_id")
    asset_id_hostel = fields.Many2one('medcell.asset.product.room', 'Asset')
    product_sub_category = fields.Many2one('medcell.product.sub.category', string='Product Sub Category',
                                           related="group_id.product_sub_category_id")
    product_name = fields.Char(string='Name')
    product_code = fields.Char(string=' Product Code')
    company_id = fields.Many2one('res.company', 'Institution')
    sequencing_digit = fields.Char(string='Sequence Digit')

    code = fields.Char(string="Code")
    serial_no = fields.Char(string="Model/Serial No")
    purchase_date = fields.Date(string="Purchase Date")
    vendor_name = fields.Many2one('res.partner', string="Supplier/Vendor Name")
    invoice_no = fields.Char(string="Invoice Number")
    warranty_period = fields.Char(string="Warranty Period")
    warranty_expires = fields.Date(string="Warranty Expires")
    brand_id = fields.Many2one('medcell.asset.brand', string="Brand")
    description = fields.Char(string="Description")
    asset_move_return_ids = fields.One2many('asset.move.return.details', 'product_id', readonly=True)
    state = fields.Selection([('instock', 'In Stock'), ('issued', 'Issued')], string="Status")

    is_sponsored = fields.Boolean('Sponsored', default=False)
    sponsored_by = fields.Char(string="Sponsored By")
    sponsor_mobile = fields.Char(string='Mobile')
    sponsor_email = fields.Char(string='Email')
    date_of_sponsoring = fields.Date(string='Date')
    sponsor_street = fields.Char()
    sponsor_street2 = fields.Char()
    sponsor_city1 = fields.Char()
    sponsor_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    sponsor_country = fields.Many2one('res.country', string='Country', ondelete='restrict')
    sponsor_zip = fields.Char(change_default=True)
    group_id = fields.Many2one('medcell.products.group', string="Group")
    is_manually = fields.Boolean(string="Manually")
    qr_product = fields.Binary('QR Product')
    qr_product_name = fields.Char(default="product_qr.png")
    asset_name = fields.Char(string="Product Name", required=True)

    building_id = fields.Many2one('medcell.asset.building', string="Building")
    block_id = fields.Many2one('medcell.asset.block', string="Block")
    floor_id = fields.Many2one('medcell.asset.floor', string='Floor')
    room_id = fields.Many2one('medcell.asset.product.room', string="Room")
    cabin_name = fields.Char(string="Cabin Name", related="room_id.room_name")
    sequence = fields.Char(string="Serial No", readonly=True, compute="sequence_no")

    @api.model
    def name_get(self):
        return [(record.id,
                 "[%s] %s" % (record.product_code, record.group_id.name) if record.product_code else record.group_id)
                for record in self]

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('product_code', operator, name)]
        ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()

    @api.model
    def create(self, vals):
        res = super(medcellProduct, self).create(vals)
        if self.user_has_groups("medcell_asset_management.group_products_create"):
            res.sequence = self.env['ir.sequence'].next_by_code('asset.product.sequence')
            res.state = 'instock'
            res.ensure_one()
            if not res.is_manually:
                res.product_code = self.env['ir.sequence'].next_by_code(res.group_id.sequence)
            # Qrcode Generation
            if not qrcode or not base64:
                raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            name = res.product_code + '_Product.png'
            if res.product_code and res.product_category.cat_name and res.product_sub_category.sub_cat_name:
                qr.add_data(
                    res.product_code + ' | ' + res.product_category.cat_name + ' | ' + res.product_sub_category.sub_cat_name)
            else:
                raise UserError('Please add Asset code, Product Category, Product Sub Category for generate Qr code')
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            res.write({'qr_product': qr_image, 'qr_product_name': name})
        else:
            raise ValidationError("Sorry, you are not allowed to create a record.")
        return res

    def unlink(self):
        if not self.user_has_groups("medcell_asset_management.group_products_delete"):
            raise ValidationError("Sorry, you are not allowed to delete the Record.")
        return super(medcellProduct, self).unlink()

    def product_details_mapping(self):
        for asset in self:
            product = self.env['asset.product.details'].search([('product_id', '=', asset.id),
                                                                ('product_code', '=', asset.product_code)])
            asset.update({
                'company_id': product.room_id.company_id.id,
                'building_id': product.room_id.building_id.id,
                'block_id': product.room_id.block_id.id,
                'floor_id': product.room_id.floor_id.id,
                'room_id': product.room_id.id
            })

    @api.depends('asset_name')
    def sequence_no(self):
        no = 0
        for l in self:
            no = no + 1
            l.sequence = no


class AssetMoveIssueDetails(models.Model):
    _name = 'asset.move.return.details'

    custodian_id = fields.Many2one('hr.employee', string="Custodian Name")
    issue_date = fields.Date(string="Handover Date")
    returned_date = fields.Date(string="Return Date")
    product_id = fields.Many2one('asset.product', string="Product")
