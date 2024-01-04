# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PaymentHistoryLine(models.Model):
    _name = 'aml.payment.history.line'
    _description = "Account Move Line Payment History Line"
    _rec_name = "move_line_id"
    _order = "create_date DESC"

    payment_history_id = fields.Many2one("aml.payment.history", string="Payment History", index=True, ondelete="cascade")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    resource_id = fields.Many2one('medical.resource', compute="_compute_resource_id", store=True)
    amount = fields.Float("Amount")
    product_id = fields.Many2one(related="payment_history_id.medical_order_line_id.product_id")

    active = fields.Boolean(related="payment_history_id.active", store=True)
    payment_date = fields.Date(related="payment_history_id.payment_date", store=True)

    move_line_id = fields.Many2one(
        related="payment_history_id.move_line_id", string="Account Move Line", index=True,
        required=True, ondelete="cascade")
    invoice_id = fields.Many2one(related="move_line_id.move_id", store=True)
    is_insurance_invoice = fields.Boolean(related="invoice_id.is_insurance_invoice", store=True)
    company_id = fields.Many2one(related="move_line_id.company_id", store=True)

    medical_order_line_id = fields.Many2one(related="move_line_id.medical_order_line_id", string="Appointment Service")
    medical_order_id = fields.Many2one(related="medical_order_line_id.order_id", string="Appointment", store=True, index=True)
    medical_order_clinic_id = fields.Many2one(related='medical_order_id.clinic_id', string="Clinic", store=True, index=True)

    @api.depends('analytic_account_id')
    def _compute_resource_id(self):
        Resource = self.env['medical.resource']
        for rec in self:
            rec.resource_id = Resource.search([('analytic_account_id', '=', rec.analytic_account_id.id)], limit=1)


class PaymentHistory(models.Model):
    _name = 'aml.payment.history'
    _description = "Account Move Line Payment History"
    _rec_name = "move_line_id"
    _order = "create_date DESC"

    payment_ids = fields.Many2many(
        "account.payment", "account_payment_aml_payment_history_rel",
        "aml_payment_history_id", "account_payment_id",
        string="Payment", index=True,
        required=True, ondelete="cascade")
    payment_date = fields.Date("Payment Date", default=fields.Date.today)
    move_line_id = fields.Many2one(
        "account.move.line", string="Account Move Line", index=True,
        required=True, ondelete="cascade")
    company_id = fields.Many2one(related="move_line_id.company_id", store=True)
    amount = fields.Float("Amount")
    active = fields.Boolean(default=True)
    cancel_date = fields.Date("InActive Date")
    line_ids = fields.One2many(
        "aml.payment.history.line", "payment_history_id", string="Distribution Lines",
        ondelete="cascade")

    invoice_id = fields.Many2one(related="move_line_id.move_id", store=True)
    is_insurance_invoice = fields.Boolean(related="invoice_id.is_insurance_invoice", store=True)

    medical_order_line_id = fields.Many2one(related="move_line_id.medical_order_line_id", string="Appointment Service")
    medical_order_id = fields.Many2one(related="medical_order_line_id.order_id", string="Appointment")
    medical_order_resource_id = fields.Many2one(related='medical_order_id.resource_id', string="Resource")
    medical_order_clinic_id = fields.Many2one(related='medical_order_id.clinic_id', string="Clinic")

    # analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    def add_line(self, account_id, amount):
        self.ensure_one()
        return self.line_ids.create({
            'payment_history_id': self.id,
            'analytic_account_id': account_id,
            'amount': amount,
        })

    @api.model
    def create(self, vals):
        record = super(PaymentHistory, self).create(vals)
        amount = vals.get('amount')
        move_line = record.move_line_id
        if amount and move_line:
            if move_line.analytic_tag_ids:
                for tag in record.move_line_id.analytic_tag_ids:
                    for tag_line in tag.analytic_distribution_ids:
                        acc_share = amount * tag_line.percentage / 100.0
                        record.add_line(tag_line.account_id.id, acc_share)

            if move_line.analytic_account_id:
                record.add_line(move_line.analytic_account_id.id, amount)
        return record

    def write(self, vals):
        if vals.get('active') and vals['active'] == False:
            vals['cancel_date'] = fields.Date.today()
        return super(PaymentHistory, self).write(vals)


class AccountMovePayment(models.Model):
    _name = 'account.move.payment.link'
    _description = "Account Move Line Payment"

    payment_id = fields.Many2one(
        "account.payment", string="Payment", index=True,
        required=True, ondelete="cascade")
    payment_date = fields.Date(related="payment_id.payment_date", store=True)

    move_line_id = fields.Many2one(
        "account.move.line", string="Account Move Line", index=True,
        required=True, ondelete="cascade")
    invoice_id = fields.Many2one(related="move_line_id.move_id")

    medical_order_line_id = fields.Many2one(related="move_line_id.medical_order_line_id", string="Appointment Service")
    medical_order_id = fields.Many2one(related="medical_order_line_id.order_id", string="Appointment")
    medical_order_resource_id = fields.Many2one(related='medical_order_id.resource_id', string="Resource")
    medical_order_clinic_id = fields.Many2one(related='medical_order_id.clinic_id', string="Clinic")

    amount = fields.Float("Amount")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(related="move_line_id.company_id", store=True)
