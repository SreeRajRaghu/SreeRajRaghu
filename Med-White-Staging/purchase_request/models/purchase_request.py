from odoo import fields, models, api, _
from datetime import datetime

from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = "Purchase Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', readonly=True, tracking=True)
    requested_date = fields.Date('Requested Date', tracking=True)
    expected_date = fields.Date('Expected Receipt date', tracking=True)
    user_id = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user.id, tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch", tracking=True, default=lambda self: self.env.user.branch_id.id)
    order_line_ids = fields.One2many('product.request.line', 'purchase_req_id', string="Order Line", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('forward', 'Forward'),
        ('reject', 'Reject'),
        ('finance', 'Finance'),
        ('approved', 'Approved')
    ], string='State', default='draft', tracking=True)
    is_checked = fields.Boolean(string='Availability Checked?')
    is_issued = fields.Boolean(string='Is Issued')
    stock_picking_ids = fields.One2many('stock.picking', 'purchase_request_id', tracking=True)
    purchase_agreement_id = fields.Many2one('purchase.requisition', 'purchase Agreement')
    
    @api.model
    def create(self, vals_list):
        res = super(PurchaseRequest, self).create(vals_list)
        year = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d').strftime('%y')
        month = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d').strftime('%m')
        seq = 'PR' + '/' + year + '/' + month + '/' + str(self.env['ir.sequence'].next_by_code('purchase.request'))
        res.name = seq
        return res

    def action_purchase_agreement(self):
        return {
            'name': 'Purchase Agreements',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'purchase.requisition',
            'res_id': self.purchase_agreement_id.id
        }

    def action_in_request(self):
        for rec in self:
            rec.state = 'requested'

    def action_to_finance(self):
        for rec in self:
            rec.state = 'finance'

    def action_to_ceo_rejected(self):
        for rec in self:
            rec.state = 'reject'

    def action_forward_to_ceo(self):
        for rec in self:
            rec.state = 'forward'

    def action_to_forward(self):
        for rec in self:
            rec.state = 'finance'

    def action_to_approved_request(self):
        for rec in self:
            rec.state = 'approved'

    def action_to_approved(self):
        for rec in self:
            purchase_agreement = self.env['purchase.requisition']
            agreement = purchase_agreement.create({
                'type_id': 2,
                'user_id': rec.user_id.id,
                'ordering_date': rec.requested_date,
                'origin': rec.name,
                'branch_id': rec.branch_id.id,
                'schedule_date': rec.expected_date,
                'line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'product_qty': line.product_qty,
                }) for line in rec.order_line_ids.filtered(lambda lines: not lines.is_issued)],
            })
            rec.purchase_agreement_id = agreement.id
            rec.state = 'approved'

    def action_to_approve(self):
        for rec in self:
            purchase_agreement = self.env['purchase.requisition']
            agreement = purchase_agreement.create({
                'type_id': 2,
                'user_id': rec.user_id.id,
                'ordering_date': rec.requested_date,
                'origin': rec.name,
                'branch_id': rec.branch_id.id,
                'schedule_date': rec.expected_date,
                'line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'product_qty': line.product_qty,
                }) for line in rec.order_line_ids.filtered(lambda lines: not lines.is_issued)],
            })
            rec.purchase_agreement_id = agreement.id
            rec.state = 'approved'

    def action_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_check_availability(self):
        for rec in self:
            location = self.env.user.company_id.location_id.id
            if not location:
                raise UserError(_('Please select internal location for general settings'))
            for data in rec.mapped('order_line_ids'):
                product = data.product_id
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location)
                ])
                data.available_qty = sum(quant.quantity for quant in quants)
        self.is_checked = True
    
    def action_reject_by_finance(self):
        for record in self:
            log_note = "<span style='color: red;'>Rejected From Finance Dept.</span>"
            record.message_post(body=log_note, subtype='mt_note')
            record.state = 'forward'


class RequestProductLines(models.Model):
    _name = 'product.request.line'

    product_id = fields.Many2one('product.product', string='Product', tracking=True)
    product_qty = fields.Float(string='Quantity', default=1, tracking=True)
    available_qty = fields.Float(string='Available Quantity', tracking=True)
    changed_qty = fields.Float(string='Change To', tracking=True)
    product_uom_id = fields.Many2one(related='product_id.uom_id', tracking=True)
    purchase_req_id = fields.Many2one('purchase.request', string="Order Request", tracking=True)
    state = fields.Selection(related='purchase_req_id.state', tracking=True)
    is_issued = fields.Boolean(string='Issued', tracking=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    purchase_request_id = fields.Many2one('purchase.request')
