# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MedCustomerPackage(models.Model):
    _name = 'medical.customer.package'
    _description = "Medical Customer Package"


class CustomerPackage(models.Model):
    _name = 'customer.package'
    _description = "Medical Customer Package"
    _inherit = ['mail.thread']
    _order = "create_date DESC"

    name = fields.Char(string="Name", required=True, translate=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    state = fields.Selection(
        [('running', 'Running'), ('done', 'Finished'), ('cancel', 'Cancelled'), ('hold', 'On Hold')],
        string='State', default='running', tracking=1)
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    invoice_id = fields.Many2one(
        'account.move', string="Invoice", tracking=True,
        domain="[('type', '=', 'out_invoice'), ('is_patient_invoice','=',True), ('partner_id', '=', partner_id)]")
    session_total = fields.Integer("Total Sessions", tracking=True)
    session_done = fields.Integer("Completed Sessions", tracking=True, compute="_compute_remaining", store=True)
    session_remaining = fields.Integer("Remaining Sessions", tracking=True, compute="_compute_remaining", store=True)
    session_price = fields.Float("Session Price", tracking=True)
    duration = fields.Float("Duration", tracking=True)
    product_id = fields.Many2one("product.product", string="Service", tracking=True)
    medical_order_id = fields.Many2one(
        'medical.order', string="Added from Appointment", tracking=True,
        domain="[('partner_id', '=', partner_id)]")
    medical_order_line_ids = fields.One2many('medical.order.line', 'related_pkg_id', tracking=True, string="Service Lines")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    @api.depends('medical_order_line_ids', 'session_total', 'partner_id', 'state')
    def _compute_remaining(self):
        for rec in self:
            line_count = len(rec.medical_order_line_ids.ids)
            rec.session_done = line_count
            rec.session_remaining = rec.session_total - line_count

    def auto_pkg_done(self):
        self.search([('session_remaining', '=', 0)]).write({'state': 'done'})
        # self.filtered(lambda r: r.session_remaining == 0 and r.state != "done").write({"state": "done"})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_pause(self):
        self.write({'state': 'hold'})

    def action_running(self):
        self.write({'state': 'running'})
