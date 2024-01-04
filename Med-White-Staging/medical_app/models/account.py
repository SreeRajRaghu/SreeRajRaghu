# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AccPayment(models.Model):
    _inherit = "account.payment"

    medical_order_id = fields.Many2one("medical.order", string="Appointment", domain="[('partner_id', '=', partner_id)]")
    session_id = fields.Many2one("medical.session", string="Session")
    # session_id = fields.Many2one("medical.session", related="medical_order_id.session_id", string="Session", store=True)
    paid_move_line_ids = fields.Many2many(
        'account.move.line', 'account_payment_move_line_rel',
        'payment_id', 'move_line_id', string="Move Lines")
    med_employee_id = fields.Many2one("hr.employee", string="Employee")

    @api.model
    def create(self, vals):
        if self.env.context.get('default_med_employee_id') and not vals.get('med_employee_id'):
            vals['med_employee_id'] = self.env.context['default_med_employee_id']
        return super(AccPayment, self).create(vals)


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_comment = fields.Text("Payment Comments")
    resource_id = fields.Many2one('medical.resource', string='Resource', tracking=True)
    file_no = fields.Char(related="partner_id.file_no")
    file_no2 = fields.Char(related="partner_id.file_no2")
    medical_order_id = fields.Many2one("medical.order", string="Appointment", tracking=True)
    visit_opt_id = fields.Many2one(related='medical_order_id.visit_opt_id', string='Visit Option', store=True)
    session_id = fields.Many2one(related="medical_order_id.session_id", string="Session")
    insurance_card_id = fields.Many2one("insurance.card", readonly=True, tracking=True)
    ref_invoice_id = fields.Many2one('account.move', 'Ref. Invoice', tracking=True)
    ref_invoice_partner_id = fields.Many2one(related="ref_invoice_id.partner_id", string="Ref. Contact", tracking=True)
    is_insurance_invoice = fields.Boolean(tracking=True)
    is_patient_invoice = fields.Boolean(tracking=True)
    med_employee_id = fields.Many2one("hr.employee", string="Employee", tracking=True)
    posted_date = fields.Datetime(string='Posted Date')
    incident_approval_no = fields.Char("Incident / SSNBR / Approval")

    def action_invoice_register_payment(self):
        order_id = self.medical_order_id.id
        return super(AccountMove, self.with_context(
            default_medical_order_id=order_id, medical_order_id=order_id)).action_invoice_register_payment()

    @api.onchange('medical_order_id')
    def _onchange_medical_order_id(self):
        if self.medical_order_id:
            self.insurance_card_id = self.medical_order_id.insurance_card_id.id

    @api.model
    def create(self, vals):
        if self.env.context.get('default_med_employee_id') and not vals.get('med_employee_id'):
            vals['med_employee_id'] = self.env.context['default_med_employee_id']
        record = super(AccountMove, self).create(vals)
        if record.medical_order_id.invoice_note:
            record.comment = record.medical_order_id.invoice_note

        return record

    def action_post(self):
        self.medical_order_id.check_insurance_expiry(self.invoice_date)
        res = super(AccountMove, self).action_post()
        if self.type == 'out_invoice' and self.is_patient_invoice and self.insurance_card_id:
            self.with_context(ignore_warning=True).action_create_insurance_invoice()

        orders = self.invoice_line_ids.mapped('medical_order_id')
        orders.create_picking()
        self.write({'posted_date': fields.datetime.now()})
        return res

    def action_create_insurance_invoice(self):
        # if self.ref_invoice_id:
        #     raise UserError(_('Insurance Bill is already created.'))  # or we can ignore it
        if not self.is_patient_invoice:
            raise UserError(_('There must be a Patient Invoice.'))  # or we can also ignore it

        insurance_invoice = self.medical_order_id.create_insurance_invoice()
        self.ref_invoice_id = insurance_invoice.id
        return self.medical_order_id.action_view_bill()

    def js_assign_outstanding_line(self, line_id):
        res = super(AccountMove, self).js_assign_outstanding_line(line_id)
        self.env['account.move.line'].browse(line_id).payment_id.write({'medical_order_id': self.medical_order_id.id})
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    medical_order_line_id = fields.Many2one("medical.order.line", string="Appointment Service")
    medical_order_id = fields.Many2one(related="medical_order_line_id.order_id", string="Appointment")
    session_count = fields.Integer("Session Count")
    # related_pkg_id = fields.Many2one(related="medical_order_line_id.related_pkg_id")
    # consumable_ids = fields.Many2many(
    #     'product.product', 'invoice_line_product_consumable_rel', 'invoice_id', 'product_id',
    #     string='Consumables', domain=[('is_medical_consumable', '=', True)])
    # has_insurance = fields.Boolean('Has Insurance')
    # insurance_card_id = fields.Many2one('insurance.card', 'Insurance Card')
    # discount_insurance = fields.Float('Insurance Discount', readonly=True)
    # discount_fixed = fields.Float("Discount (Fixed)", digits=dp.get_precision('Product Price'), help="Fixed amount discount.")
    patient_share = fields.Float('Patient Share')

    # Product Related Fields
    # is_variant_price = fields.Boolean(related="product_id.is_variant_price", store=True)
    # p_type = fields.Selection(related='product_id.type', string="Product Type", store=True)
    # p_default_code = fields.Char(related='product_id.default_code', string="Internal Reference", store=True)
    # p_categ_id = fields.Many2one(related='product_id.categ_id', string="Category", store=True)
    # p_available_in_pos = fields.Boolean(related='product_id.available_in_pos', string="Available In PoS", store=True)
    # # p_pos_categ_id = fields.Many2one(related='product_id.pos_categ_id', string="PoS Category", store=True)
    # p_standard_price = fields.Float(related='product_id.standard_price', string="Cost", store=True)
    # p_list_price = fields.Float(related='product_id.list_price', string="Sale Price", store=True)
    # p_uom_id = fields.Many2one(related='product_id.uom_id', string="Unit of Measure(s)", store=True)
    # p_analytic_account_id = fields.Many2one(related='product_id.analytic_account_id', string="Analytic Account(s)", store=True)
    # p_duration = fields.Float(related='product_id.duration', string="Duration(s)", store=True)

    # # Medical Order Related Fields
    # # medical_date_order = fields.Datetime(related='medical_order_id.date_order', string="Date Order", store=True)
    # medical_order_resource_id = fields.Many2one(related='medical_order_id.resource_id', string="Resource", store=True)
    # medical_order_date_arrived = fields.Datetime(related='medical_order_id.date_arrived', string="Arrived Time", store=True)
    # medical_order_date_in = fields.Datetime(related='medical_order_id.date_in', string="Date In", store=True)
    # medical_order_date_out = fields.Datetime(related='medical_order_id.date_out', string="Date Out", store=True)
    # waiting_time = fields.Float(compute="_compute_appointment_duration", string="Waiting Time")
    # duration = fields.Float(compute="_compute_appointment_duration", string="Duration")

    payment_ids = fields.Many2many(
        'account.payment', 'account_payment_move_line_rel',
        'move_line_id', 'payment_id', string="Payment")
    amount_paid = fields.Float()
    amount_pay_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid')
    ], string="Pay Status", compute='_compute_amount_pay_status', store=True)
    amount_due = fields.Float("Amount Due", compute="compute_line_amount_due")

    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        if vals.get('amount_paid'):
            self.mapped("medical_order_line_id").write({'amount_paid': vals['amount_paid']})
        return res

    @api.depends("amount_paid", "price_subtotal")
    def compute_line_amount_due(self):
        for rec in self:
            rec.amount_due = rec.price_subtotal - rec.amount_paid

    # @api.depends('medical_order_id', 'medical_order_date_arrived', 'medical_order_date_in', 'medical_order_date_out')
    # def _compute_appointment_duration(self):
    #     for invoice in self:
    #         if invoice.medical_order_date_arrived and invoice.medical_order_date_in and invoice.medical_order_date_out:
    #             diff = invoice.medical_order_date_out - invoice.medical_order_date_in
    #             if diff:
    #                 duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
    #                 invoice.duration = round(duration, 2)
    #             diff2 = invoice.medical_order_date_in - invoice.medical_order_date_arrived
    #             if diff2:
    #                 duration2 = float(diff2.days) * 24 + (float(diff2.seconds) / 3600)
    #                 invoice.waiting_time = round(duration2, 2)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        vals = super(AccountMoveLine, self)._onchange_product_id()
        for line in self:
            product = line.product_id
            if product:
                if product.analytic_account_id:
                    line.account_analytic_id = product.analytic_account_id.id
                elif product.categ_id.analytic_account_id:
                    line.account_analytic_id = product.categ_id.analytic_account_id.id

        if len(self) == 1:
            return vals

    @api.depends('amount_paid', 'move_id.invoice_payment_state')
    def _compute_amount_pay_status(self):
        for line in self:
            if line.move_id.invoice_payment_state == 'paid':
                # line.amount_paid = line.price_total
                line.amount_pay_status = 'paid'
            elif not line.amount_paid:
                line.amount_pay_status = 'unpaid'
            elif line.amount_paid < line.price_total:
                line.amount_pay_status = 'partially_paid'
            else:
                line.amount_pay_status = 'paid'


class AnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    med_resource_id = fields.Many2one("medical.resource", string="Resource", compute="_compute_med_resource_id")
    employee_id = fields.Many2one("hr.employee", string="Employee", compute="_compute_med_resource_id")

    def _compute_med_resource_id(self):
        Resource = self.env['medical.resource']
        for rec in self:
            resource = Resource.search([('analytic_account_id', '=', rec.id)], limit=1)
            rec.med_resource_id = resource.id
            rec.employee_id = resource.hr_staff_id.id


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    resource_id = fields.Many2one('medical.resource', 'Resource', readonly=True)

    def _select(self):
        return super()._select() + ", move.resource_id as resource_id"

    def _group_by(self):
        return super()._group_by() + ", move.resource_id"
