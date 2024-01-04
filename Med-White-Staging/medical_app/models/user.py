# -*- coding: utf-8 -*-

from odoo import fields, models


class Users(models.Model):
    _inherit = 'res.users'

    company_code_list = fields.Char('Allowed Company Code', default='lab')
    branch_ids = fields.Many2many(
        "medical.clinic", "medical_clinic_users_rel",
        "res_users_id", "medical_clinic_id",
        string="Branches")

    # @api.model
    # def create(self, values):
    #     return super(Users, self.with_context(from_res_users=True)).create(values)
