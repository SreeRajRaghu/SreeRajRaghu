# -*- coding: utf-8 -*-

from odoo import fields, models


class ResourceGroup(models.Model):
    _name = 'medical.resource.group'
    _description = 'Medical Resource Group'

    name = fields.Char("Group Name", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('uniq_group_name', 'unique (name)', 'Group Name must be unique.')
    ]


class MedicalResource(models.Model):
    _name = 'medical.resource'
    _description = 'Medical Resource'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    RESOURCE_TYPE = [
        ('hr_staff', 'HR Staff'),
        ('free', 'Free'),
    ]

    name = fields.Char(required=True, translate=True, tracking=True)
    group_id = fields.Many2one("medical.resource.group", string="Group", tracking=True)
    company_id = fields.Many2one(related="group_id.company_id", store=True, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account', tracking=True)
    resource_type = fields.Selection(RESOURCE_TYPE, string='Type', tracking=True)
    hr_staff_id = fields.Many2one('hr.employee', string='HR Staff')
    working_hour_id = fields.Many2one('resource.calendar', string='Working Hours', tracking=True)
    stock_location_id = fields.Many2one('stock.location', string='Stock Location', tracking=True)
    medical_consumable_location_id = fields.Many2one('stock.location', string='Consumable Stock Location', tracking=True)
    destination_location_id = fields.Many2one('stock.location', string='Destination Location', tracking=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    note = fields.Text(tracking=True)
    phone = fields.Char(tracking=True)
    sequence = fields.Integer(default=8, required=True, tracking=True)
    blocked_patient_ids = fields.Many2many('res.partner', 'blocked_patient_by_doctor', 'resource_id', 'patient_id', string="Blocked Patients", tracking=True)

    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist", domain=[('insurance_company_id', '=', False)], tracking=True)

    emp_ids = fields.Many2many("hr.employee", string="Employees", tracking=True)
