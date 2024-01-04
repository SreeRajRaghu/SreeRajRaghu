# -*- coding: utf-8 -*-

from odoo import fields, models


class Employee(models.Model):
    _inherit = 'hr.employee'

    medical_license = fields.Char("Medical License")
    ml_issue = fields.Date("Medical License Issued")
    ml_expiry = fields.Date("Medical License Expiry")


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    medical_license = fields.Char("Medical License", readonly=True)
    ml_issue = fields.Date("Medical License Issued", readonly=True)
    ml_expiry = fields.Date("Medical License Expiry", readonly=True)
    pin = fields.Char("PIN", readonly=True)
