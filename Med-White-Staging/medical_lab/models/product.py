
from odoo import api, fields, models


class ProductProfile(models.Model):
    _name = "product.profile"
    _description = "Product Profile"

    name = fields.Char(string='Unit Name', required=True)

    _sql_constraints = [('name_uniq', 'unique(name)', 'The profile name must be unique')]


class ProductProduct(models.Model):
    _inherit = "product.template"

    medical_labtest_types_ids = fields.Many2many('medical.labtest.types', 'labtest_types_product_id', 'labtest_types_id', 'product_id',
                                                 string="Medical Labtest Types")
    prod_profile_id = fields.Many2one("product.profile", string="Product Profile")


class ProductCategory(models.Model):
    _inherit = 'product.category'

    publish = fields.Boolean(string="Publish", default=True)
    code = fields.Char('Code')
    auto_sequence = fields.Boolean(string="Auto Sequence")
    machine_code = fields.Char("Machine Code")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)


class Product(models.Model):
    _inherit = 'product.product'

    def _code_auto_sequence(self):
        Sequence = self.env['ir.sequence']
        for rec in self.filtered(lambda p: p.categ_id.auto_sequence and not p.default_code):
            last_seq = Sequence.sudo().next_by_code('medical.product.code')
            rec.default_code = "%s/%s" % (rec.categ_id.code, last_seq)

    @api.model
    def create(self, vals):
        record = super(Product, self).create(vals)
        record._code_auto_sequence()
        return record

    def write(self, vals):
        res = super(Product, self).write(vals)
        self._code_auto_sequence()
        return res


class Employee(models.Model):
    _inherit = "hr.employee"

    is_technician = fields.Boolean("Is Technician ?")


class EmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    is_technician = fields.Boolean("Is Technician ?")
