from odoo import models, api
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    def write(self, vals):
        res = super(Employee, self).write(vals)
        if 'active' in vals and not vals['active']:
            for rec in self:
                rec.contract_id.write({'state': 'close'})
        return res

    @api.constrains('identification_id')
    def _check_unique_identification_id(self):
        # identification_id = self.filtered('identification_id').mapped('identification_id')
        for emp in self.filtered('identification_id'):
            add_sql = ""
            if emp.company_id:
                add_sql = "AND e.company_id = %s" % (emp.company_id.id)
            sql = """
                SELECT e.id, e.name FROM
                hr_employee as e WHERE e.active is true AND e.id NOT IN %s AND e.identification_id = %s """ + add_sql + """ LIMIT 1"""
            self.env.cr.execute(sql, (tuple(emp.ids), emp.identification_id))
            records = self.env.cr.fetchone()
            if records:
                raise ValidationError("Employee Number is already assigned to %s." % (records[1]))
