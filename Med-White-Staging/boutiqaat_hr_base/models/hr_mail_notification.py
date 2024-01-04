# -*- coding: utf-8 -*-

from odoo import fields, models


class HrRecruitmentNotification(models.Model):
    _name = 'hr.mail.notification'
    _description = "HR Mail Notification"

    name = fields.Char('Name', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
