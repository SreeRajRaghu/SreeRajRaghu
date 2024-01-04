# coding: utf-8

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    license_ed = fields.Date('Company License Expiration Date')
    ministry_auth_sign_ed = fields.Date('Ministry Authorization Signature Expiration Date')
    gov_sal_cert_ed = fields.Date('Governmental Salary Certificate Expiration Date')
    gov_med_license_cert_ed = fields.Date('Governmental Medical License Certificate Expiration Date')


class Calendar(models.Model):
    _inherit = 'resource.calendar'

    month_days = fields.Float("Month Days", default=26)
    prob_period_days = fields.Integer("Probation Days", default=100)
    prob_exclude_off = fields.Boolean("Probation period exclude Off Days ?")
