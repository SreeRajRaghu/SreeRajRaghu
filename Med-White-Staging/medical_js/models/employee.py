# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError


class Employee(models.Model):
    _inherit = 'hr.employee'

    clinic_id = fields.Many2one("medical.clinic", string="Branch")
    is_medical_user = fields.Boolean("Is Session User ?")
    max_discount = fields.Float("Maximum Allowed Discount")

    @api.model
    def create(self, vals_list):
        company = self.env.user.company_id
        if company.employee_seq_id:
            vals_list['identification_id'] = self.get_next_employee_code()
        vals_list['identification_id'] = self.env['ir.sequence'].next_by_code('hr.employee')
        return super(Employee, self).create(vals_list)

    def get_next_employee_code(self):
        company = self.env.user.company_id
        if company.employee_seq_id:
            return company.employee_seq_id._next()
        else:
            raise UserError('Patient File Sequence is missing')



class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    clinic_id = fields.Many2one("medical.clinic", readonly=True)
    is_medical_user = fields.Boolean("Is Session User ?", readonly=True)
    max_discount = fields.Float(readonly=True)
