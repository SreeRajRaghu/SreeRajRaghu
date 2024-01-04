# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from collections import defaultdict
# from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from odoo.tools import float_is_zero


class MedicalSession(models.Model):
    _name = 'medical.session'
    _order = 'id desc'
    _description = 'Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    POS_SESSION_STATE = [
        ('new_session', 'New Session'),
        ('opening_control', 'Opening Control'),  # method action_pos_session_open
        ('opened', 'In Progress'),               # method action_pos_session_closing_control
        ('closing_control', 'Closing Control'),  # method action_pos_session_close
        ('closed', 'Closed & Posted'),
    ]

    company_id = fields.Many2one('res.company', related='config_id.company_id', string="Company", readonly=True)

    config_id = fields.Many2one(
        'medical.config', string='Scheduler',
        required=True,
        index=True)
    clinic_id = fields.Many2one(related="config_id.clinic_id", string='Branch')

    name = fields.Char(string='Session ID', required=True, readonly=True, default='/')
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        required=True,
        index=True,
        readonly=True,
        states={'opening_control': [('readonly', False)]},
        default=lambda self: self.env.uid,
        ondelete='restrict')
    currency_id = fields.Many2one('res.currency', related='config_id.currency_id', string="Currency", readonly=False)
    start_at = fields.Datetime(string='Opening Date', readonly=True)
    stop_at = fields.Datetime(string='Closing Date', readonly=True, copy=False)

    state = fields.Selection(
        POS_SESSION_STATE, string='Status',
        required=True, readonly=True,
        index=True, copy=False, default='new_session')

    statement_ids = fields.One2many("medical.session.statement", "session_id", string="Statements")

    order_ids = fields.One2many('medical.order', 'session_id',  string='Orders')
    order_count = fields.Integer(compute='_compute_order_count')
    picking_count = fields.Integer(compute='_compute_picking_count')

    invoice_ids = fields.One2many(
        'account.move', 'session_id',  string='Invoices', domain=[('is_patient_invoice', '=', True)])
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    ins_invoice_ids = fields.One2many(
        'account.move', 'session_id',  string='Ins.Invoices', domain=[('is_insurance_invoice', '=', True)])
    ins_invoice_count = fields.Integer(compute='_compute_invoice_count')

    payment_method_ids = fields.Many2many(related='config_id.journal_ids', string='Payment Methods')
    total_payments_amount = fields.Float(compute='_compute_total_payments_amount', string='Total Payments Amount')
    is_in_company_currency = fields.Boolean('Is Using Company Currency', compute='_compute_is_in_company_currency')
    payment_ids = fields.One2many("account.payment", "session_id", string="Payments")
    company_code = fields.Selection(related="company_id.company_code")

    _sql_constraints = [('uniq_name', 'unique(name)', "The name of this POS Session must be unique !")]

    def _compute_invoice_count(self):
        for rec in self:
            rec.ins_invoice_count = len(rec.ins_invoice_ids.ids)
            rec.invoice_count = len(rec.invoice_ids.ids)

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_is_in_company_currency(self):
        for session in self:
            session.is_in_company_currency = session.currency_id == session.company_id.currency_id

    @api.depends('payment_ids.amount')
    def _compute_total_payments_amount(self):
        for session in self:
            session.total_payments_amount = sum(session.payment_ids.mapped('amount'))

    def _compute_order_count(self):
        orders_data = self.env['medical.order'].read_group([('session_id', 'in', self.ids)], ['session_id'], ['session_id'])
        sessions_data = {order_data['session_id'][0]: order_data['session_id_count'] for order_data in orders_data}
        for session in self:
            session.order_count = sessions_data.get(session.id, 0)

    def _compute_picking_count(self):
        for session in self:
            pickings = session.order_ids.mapped('picking_id').filtered(lambda x: x.state != 'done')
            session.picking_count = len(pickings.ids)

    def action_stock_picking(self):
        pickings = self.order_ids.mapped('picking_id').filtered(lambda x: x.state != 'done')
        action_picking = self.env.ref('stock.action_picking_tree_ready')
        action = action_picking.read()[0]
        action['context'] = {}
        action['domain'] = [('id', 'in', pickings.ids)]
        return action

    # @api.depends('config_id', 'statement_ids', 'payment_method_ids')
    # def _compute_cash_all(self):
    #     # Only one cash register is supported by point_of_sale.
    #     for session in self:
    #         session.cash_journal_id = session.cash_register_id = session.cash_control = False
    #         cash_payment_methods = session.payment_method_ids.filtered('is_cash_count')
    #         if not cash_payment_methods:
    #             continue
    #         for statement in session.statement_ids:
    #             if statement.journal_id == cash_payment_methods[0].cash_journal_id:
    #                 session.cash_control = session.config_id.cash_control
    #                 session.cash_journal_id = statement.journal_id.id
    #                 session.cash_register_id = statement.id
    #                 break  # stop iteration after finding the cash journal

    @api.constrains('config_id')
    def _check_pos_config(self):
        if self.search_count([
                ('state', '!=', 'closed'),
                ('config_id', '=', self.config_id.id),
            ]) > 1:
            raise ValidationError(_("Another session is already opened for this Scheduler."))

    @api.constrains('start_at')
    def _check_start_date(self):
        for record in self:
            company = record.config_id.journal_id.company_id
            start_date = record.start_at.date()
            if (company.period_lock_date and start_date <= company.period_lock_date)\
                    or (company.fiscalyear_lock_date and start_date <= company.fiscalyear_lock_date):
                raise ValidationError(_("You cannot create a session before the accounting lock date."))

    @api.model
    def create(self, values):
        config_id = values.get('config_id') or self.env.context.get('default_config_id')
        if not config_id:
            raise UserError(_("You should assign a Session Scheduler to your session."))

        config = self.env['medical.config'].browse(config_id)
        ctx = dict(self.env.context, company_id=config.company_id.id)

        values['name'] = self.env['ir.sequence'].with_context(ctx).next_by_code('medical.session')
        statement_lines = []
        for journal in config.journal_ids:
            statement_lines.append((0, 0, {
                'journal_id': journal.id,
                'config_id': config_id,
            }))

        values.update({
            'statement_ids': statement_lines,
            'config_id': config_id,
        })

        record = super(MedicalSession, self.with_context(ctx)).create(values)
        record.action_pos_session_open()
        return record

    def unlink(self):
        # for session in self.filtered(lambda s: s.statement_ids):
        #     session.statement_ids.unlink()
        raise UserError(_('Session cannot be Deleted.'))
        # return super(MedicalSession, self).unlink()

    def action_view_ins_invoices(self):
        self.ensure_one()
        action = self.env.ref('medical_app.action_move_insurance_invoice_type').read()[0]
        action.update({
            'domain': [('id', 'in', self.ins_invoice_ids.ids)]
        })
        return action

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref('medical_app.action_move_patient_out_invoice_type').read()[0]
        action.update({
            'domain': [('id', 'in', self.invoice_ids.ids)]
        })
        return action

    def action_pos_session_open(self):
        sessions = self.filtered(lambda session: session.state in ('new_session', 'opening_control'))
        sessions.write({'start_at': fields.Datetime.now(), 'state': 'opened'})
        return True

    def action_session_validate(self):
        return self._session_validate()

    def _session_validate(self):
        self.ensure_one()
        self._check_if_no_draft_orders()
        self.write({'state': 'closed', 'stop_at': fields.Datetime.now()})
        self.config_id.write({'state': 'draft', 'user_id': False, 'last_closing_date': fields.Datetime.now()})
        return {}

    def action_show_payments_list(self):
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('session_id', '=', self.id)],
            'context': {'search_default_group_by_payment_method': 1}
        }

    def open_frontend_cb(self):
        """Open the pos interface with config_id as an extra argument.

        In vanilla PoS each user can only have one active session, therefore it was not needed to pass the config_id
        on opening a session. It is also possible to login to sessions created by other users.

        :returns: dict
        """
        if not self.ids:
            return {}
        return self.config_id.open_ui()

    def action_view_order(self):
        return {
            'name': _('Appointments'),
            'res_model': 'medical.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('medical_app.view_medical_order_tree').id, 'tree'),
                (self.env.ref('medical_app.view_medical_order_form').id, 'form'),
                ],
            'type': 'ir.actions.act_window',
            'domain': [('session_id', 'in', self.ids)],
        }

    def _check_if_no_draft_orders(self):
        draft_orders = self.order_ids.filtered(lambda order: order.patient_invoice_id.state == 'draft')
        if draft_orders:
            raise UserError(_(
                    'There are still some appointment invoice(s) in draft state in the session. '
                    'Pay or cancel the following orders to validate the session:'
                    '\nAppointments:\n%s'
                ) % ', '.join(draft_orders.mapped('name'))
            )
        return True


class MedicalSessionStatement(models.Model):
    _name = 'medical.session.statement'
    _description = 'Session Statement'
    _order = 'id desc'

    journal_id = fields.Many2one(
        "account.journal", string="Journal", required=True,
        domain="[('type', 'in', ('cash', 'bank'))]")
    payment_ids = fields.One2many("account.payment", "session_id", string="Payments")
    order_ids = fields.One2many("medical.order", "session_id", string="Appointments", domain="[('session_id', '=', session_id)]")
    amount_total = fields.Float("Amount", compute="_compute_amount")
    amount_paid = fields.Float("Received Amount", compute="_compute_amount")
    session_id = fields.Many2one("medical.session", string="Session")
    config_id = fields.Many2one("medical.config", string="Configuration")

    @api.depends("order_ids.net_total")
    def _compute_amount(self):
        for rec in self:
            rec.amount_total = sum(rec.order_ids.mapped('net_total'))
            rec.amount_paid = sum(rec.order_ids.mapped('amount_paid'))
