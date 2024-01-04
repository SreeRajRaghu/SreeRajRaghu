# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

JS_MIN_READ_FIELDS = ['name', 'card_no', 'card_balance', 'balance']


class PrepaidCard(models.Model):
    _name = 'partner.prepaid.card'
    _description = "Partner Prepaid Card"
    _inherit = ['mail.thread']

    name = fields.Char(default='/Auto', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    med_invoice_ids = fields.One2many("account.move", "prepaid_card_id", string="Appointment Invoices")
    payment_ids = fields.One2many("account.payment", "prepaid_card_id", string="Payments")
    card_no = fields.Char("Card No.")
    card_balance = fields.Float("Balance (Old System)")
    balance = fields.Float("Balance", compute="compute_balance", store=True)

    @api.depends('payment_ids', 'payment_ids.amount', 'payment_ids.payment_history_ids', 'payment_ids.payment_history_ids.amount')
    def compute_balance(self):
        for rec in self:
            payments = rec.payment_ids
            plus = sum(payments.mapped('amount'))
            minus = sum(payments.mapped('payment_history_ids.amount'))
            rec.balance = plus - minus

    def check_card_no_exist(self, ignore_id, card_no):
        sql = "SELECT partner_id FROM partner_prepaid_card WHERE card_no = '%s' AND id != %s LIMIT 1" % (card_no, ignore_id)
        self.env.cr.execute(sql)
        return self.env.cr.fetchone()

    @api.constrains('card_no')
    def check_card_no(self):
        for rec in self.filtered('card_no'):
            card_ids = self.check_card_no_exist(rec.id, rec.card_no)
            if card_ids:
                partner = self.env['res.partner'].browse(card_ids[0])
                raise UserError(_('Card Number already assigned to `%s`.') % partner.name)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('partner.prepaid.card')
        return super(PrepaidCard, self).create(values)

    def fetch_prepaid_card_details(self):
        self.ensure_one()
        prepaid_card_data = {}
        prepaid_card_data = self.read(
            JS_MIN_READ_FIELDS +
            ['partner_id', 'payment_ids'])[0]
        prepaid_card_data.update({
            'invoices': self.payment_ids.mapped('payment_history_ids').read(['payment_date', 'amount', 'move_line_id', 'medical_order_id']),
            'payments': self.payment_ids.read([
                'name', 'amount', 'journal_id', 'payment_date', 'state']),
        })
        return prepaid_card_data

    @api.model
    def check_and_create_card(self, partner_id, card_no):
        self.create({
            "partner_id": partner_id,
            'card_no': card_no
        })
        return self.search_read([
            ('partner_id', '=', partner_id)],
            JS_MIN_READ_FIELDS, order="id DESC")

    # @api.model
    # def js_card_payment(self, payment_by_cards, move_lines):
    #     """ Todo Reconcile payments from card """
    #     move_lines = move_lines or {}
    #     payment_by_cards = payment_by_cards or {}

    #     amount_by_line = {}
    #     tot_amount = 0
    #     for line_id, amount in move_lines.items():
    #         amount_by_line[int(line_id)] = amount
    #         tot_amount += amount

    #     print ('_ amount_by_line : ', amount_by_line)

    #     card_by_line = {}
    #     tot_amount = 0
    #     for card_id, amount in payment_by_cards.items():
    #         card_by_line[int(card_id)] = amount
    #         tot_amount += amount

    #     cards = self.browse(list(card_by_line.keys()))

    #     print ('_ card_by_line : ', card_by_line)

    #     for card in cards:
    #         payments = card.payment_ids
    #         print ('_ payments : ', payments)
