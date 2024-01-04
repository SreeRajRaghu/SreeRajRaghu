# -*- coding: utf-8 -*-

from odoo import models, fields


class Clinic(models.Model):
    _name = 'medical.clinic'
    _description = "Clinic"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Branch", required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    resource_ids = fields.Many2many("medical.resource", string="Resources")

    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip_code = fields.Char(change_default=True, tracking=True)
    city = fields.Char(tracking=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]", tracking=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', tracking=True)
    email = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    mobile = fields.Char(tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch")

    user_ids = fields.Many2many(
        "res.users", "medical_clinic_users_rel",
        "medical_clinic_id", "res_users_id",
        string="Users", tracking=True)
