# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from .pricelist import APPLY_INS_DISC_SELECTION, APPLY_INS_DISC_STRING, APPLY_INS_DISC_HELP


DP_MEDICAL = 'Medical Price'

ORDER_STATES = [
    ('draft', _('Draft')), ('confirmed', _('Confirmed')), ('arrived', _('Arrived')),
    ('late', _('Late')), ('in', _('In')), ('out', _('Out')),
    ('invoiced', _('Invoiced')), ('paid', _('Paid')),
    ('no_answer', _('No Answer')), ('no_show', _('No Show')),
    ('done', _('Posted')), ('cancel', _('Cancelled'))
]
VISIT_TYPE = [
    ('walk_in', 'Walk In'),
    ('pre_app', 'Requested'),
]

CONSIDERATION_DATE = datetime.strptime('01-05-2020 00:00:00', '%d-%m-%Y %H:%M:%S').strftime(DEFAULT_SERVER_DATETIME_FORMAT)


class VisitOption(models.Model):
    _name = 'visit.option'
    _description = 'Visit Option'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)


class MedicalOrder(models.Model):
    _name = 'medical.order'
    _description = 'Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id DESC'

    def _default_emp(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Name', readonly=True, default=_('Draft'), copy=False, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id.id)
    date_order = fields.Datetime(string='Date', readonly=True, index=True, copy=False, default=fields.Datetime.now, tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string="Patient", required=True, tracking=50,
        domain=[("is_insurance_company", '=', False)])
    company_code = fields.Selection(related="config_id.company_code", store=True)

    visit_type = fields.Selection(VISIT_TYPE, string="Visit Type")
    visit_opt_id = fields.Many2one('visit.option', string='Visit Option', tracking=45)

    start_time = fields.Datetime(string='Start', default=fields.Datetime.now, tracking=50, copy=False)
    end_time = fields.Datetime(string='End', compute="_compute_tot_duration", store=True, tracking=45)
    total_duration = fields.Float(string="Total Duration", compute="_compute_tot_duration", store=True, tracking=True)
    resource_id = fields.Many2one('medical.resource', ondelete='restrict', string='Resource', tracking=45)

    state = fields.Selection(ORDER_STATES, default='draft', tracking=40, copy=False)
    state_color = fields.Char("State Color", compute="_compute_state_color", store=True)

    line_ids = fields.One2many('medical.order.line', 'order_id', string="Services", copy=True)
    amount_total = fields.Float(compute='_compute_order_total', digits=DP_MEDICAL, store=True, tracking=True)
    amount_paid = fields.Float(string="Amount Paid", compute="_compute_amount_paid", digits=DP_MEDICAL, store=True, tracking=True)
    amount_due = fields.Float(string="Amount Due", compute="_compute_amount_paid", digits=DP_MEDICAL, store=True, tracking=True)
    discount = fields.Float(compute='_compute_order_total', digits=DP_MEDICAL, store=True, tracking=True)
    net_total = fields.Float(compute='_compute_order_total', digits=DP_MEDICAL, store=True, tracking=True)
    orig_total = fields.Float(compute='_compute_order_total', digits=DP_MEDICAL, string="Actual Charges", store=True, tracking=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Scheme', tracking=True)
    patient_invoice_id = fields.Many2one('account.move', string='Patient Invoice', readonly=True, copy=False, tracking=True)
    invoice_number = fields.Char(related="patient_invoice_id.name", string="Invoice Ref", store=True)
    insurance_invoice_id = fields.Many2one('account.move', string='Insurance Invoice', readonly=True, copy=False, tracking=True)
    payment_ids = fields.One2many(
        'account.payment', 'medical_order_id',
        domain=[('state', 'in', ['posted', 'reconciled'])],
        string="Payments", copy=False, tracking=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True, copy=False, tracking=True)
    consu_picking_id = fields.Many2one('stock.picking', string='Consumable Picking', readonly=True, copy=False, tracking=True)
    is_readonly = fields.Boolean("Is Readonly", copy=False)

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_emp)
    clinic_id = fields.Many2one('medical.clinic', string='Branch', ondelete='restrict', tracking=10)

    session_id = fields.Many2one(
        'medical.session', "Medical Session", domain="[('state', '=', 'opened'), ('clinic_id','=',clinic_id)]", index=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    config_id = fields.Many2one(
        related="session_id.config_id", required=True,
        store=True, index=True, tracking=True)

    last_order_id = fields.Many2one(
        'medical.order', compute='_compute_last_order', store=True, readonly=True, copy=False,
        string="Last Appointment")
    cancellation_date = fields.Datetime('Cancellation Date', tracking=True, copy=False)
    cancel_reason = fields.Char('Reason for Cancel', tracking=True, copy=False)
    note = fields.Char(copy=False)
    invoice_note = fields.Char('Invoice Note', copy=False)

    date_confirm = fields.Datetime("Confirmation Time", copy=False, tracking=True, readonly=True)
    date_arrived = fields.Datetime("Arrived Time", copy=False)
    is_reschedule = fields.Boolean("Is Reschedule", copy=False)
    date_in = fields.Datetime("Date In", copy=False)
    date_out = fields.Datetime("Date Out", copy=False)
    date_done = fields.Datetime("Done Time", copy=False)
    is_first = fields.Boolean("First Appointment", compute="_is_first_appointment", store=True)
    handover_file_on = fields.Datetime('Sample Taken On', copy=False)
    printed_file_on = fields.Datetime('Printed File On', copy=False)
    optometrist_on = fields.Datetime('Optometrist File on', copy=False)
    handover_file_duration = fields.Char(compute='_compute_duration', store=True)
    print_file_duration = fields.Char(compute='_compute_duration', store=True)
    duration_in_arrived = fields.Float(compute='_compute_duration', string="Waiting Time", store=True)
    duration_out_in = fields.Float(compute='_compute_duration', string="Treatment Time", store=True, tracking=True)

    insurance_card_id = fields.Many2one(
        'insurance.card', string="Insurance Card",
        domain="[('partner_id', '=', partner_id), ('state', '=', 'running')]", tracking=True, copy=False)

    user_id = fields.Many2one("res.users", "Salesperson", default=lambda self: self.env.uid, required=True, tracking=True, copy=False)

    # Partner Related Fields
    file_no = fields.Char(related="partner_id.file_no", store=True, readonly=True)
    file_no2 = fields.Char(related="partner_id.file_no2", store=True, readonly=True)
    phone = fields.Char(related="partner_id.phone", store=True, readonly=True)
    mobile = fields.Char(related="partner_id.mobile", store=True, readonly=True)
    civil_code = fields.Char(related="partner_id.civil_code", store=True, readonly=True)

    is_followup = fields.Boolean("Is Follwup Appointment ?", tracking=True, copy=False)

    # Account
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')

    ins_approval_no = fields.Char("Incident / SSNBR / Approval", copy=False)
    ins_ticket_no = fields.Char("Auth / MCN / Ticket", copy=False)
    ins_ref = fields.Char("Reference / PreInvoice", copy=False)
    ins_member = fields.Char("Member ID", copy=False)

    ins_based_on = fields.Selection(related="pricelist_id.ins_based_on", store=True)

    need_pricelist_approval = fields.Boolean("Need Pricelist Approval", tracking=True)
    pricelist_approved = fields.Boolean("Pricelist Approved", tracking=True)
    pricelist_approved_user_id = fields.Many2one("res.users", string="Pricelist Approved By", tracking=True)
    pricelist_approved_date = fields.Datetime(string="Pricelist Approved On", tracking=True)

    # actual_tot_price = fields.Float("Total Actual Price")
    approved_tot_price = fields.Float(
        'Total Approved Price', help="Insurance Approved Total Price",
        compute="_compute_ins_amount", digits=DP_MEDICAL)
    payable_tot_price = fields.Float(
        "Patient Share", compute="_compute_ins_amount", digits=DP_MEDICAL,
        help="Payable Total Price = Patient Share + (Total Price - Approved Total Price)")
    ins_tot_price = fields.Float("Total Insurance Claim", digits=DP_MEDICAL, compute="_compute_ins_amount")
    waiting_list_id = fields.Many2one('app.waiting.list', string="Waiting List")
    last_action_id = fields.Many2one("last.action", string="Last Action")
    last_action_emp_id = fields.Many2one("hr.employee", string="Last Action Employee")
    last_action_dt = fields.Datetime(string="Last Action Datetime")
    complain_ids = fields.One2many("patient.complain", "appointment_id", string="Complains")
    extra_time = fields.Float("Extra Time", copy=False)
    last_action_id = fields.Many2one("last.action", string="Last Action")
    last_action_emp_id = fields.Many2one("hr.employee", string="Last Action Employee")
    last_action_dt = fields.Datetime(string="Last Action Datetime")
    complain_ids = fields.One2many("patient.complain", "appointment_id", string="Complains")
    canceled_by_cct = fields.Boolean()

    new_invoice_date = fields.Date("New Invoice Date", tracking=True)
    show_consume_button = fields.Boolean('Show Consume Button', compute='_compute_show_consume_button')

    def _compute_show_consume_button(self):
        for record in self:
            if not record.consu_picking_id and record.mapped('line_ids.consumable_ids'):
                record.show_consume_button = True
            else:
                record.show_consume_button = False

    @api.onchange('config_id', 'insurance_card_id')
    def _onchange_config_id(self):
        if self.insurance_card_id:
            self.pricelist_id = self.insurance_card_id.pricelist_id.id
        elif self.config_id.pricelist_id:
            self.pricelist_id = self.config_id.pricelist_id.id
        else:
            self.pricelist_id = self.partner_id.property_product_pricelist.id
        # To Recompute lines
        for line in self.line_ids:
            line._onchange_product_id()

    currency_rate = fields.Float(
        "Currency Rate", compute='_compute_currency_rate',
        compute_sudo=True, store=True, readonly=True,
        help='The rate of the currency to the currency of rate 1 applicable at the date of the order')

    picking_type_id = fields.Many2one('stock.picking.type', related='session_id.config_id.picking_type_id', string="Operation Type", readonly=False)
    location_id = fields.Many2one(
        comodel_name='stock.location',
        related='picking_id.location_id',
        string="Location", store=True,
        readonly=True,
    )
    nb_print = fields.Integer(string='Number of Print', readonly=True, copy=False, default=0)

    def write(self, vals):
        if vals.get('state'):
            state = vals['state']
            if state == 'confirmed':
                vals['date_confirm'] = fields.Datetime.now()
            if state == 'arrived':
                vals['date_arrived'] = fields.Datetime.now()
            if state == 'in':
                vals['date_in'] = fields.Datetime.now()
            if state == 'out':
                vals['date_out'] = fields.Datetime.now()
            if state == 'done':
                vals['date_done'] = fields.Datetime.now()
            if state == 'cancel':
                vals['cancellation_date'] = fields.Datetime.now()
        if vals.get('last_action_id'):
            vals['last_action_dt'] = fields.Datetime.now()
            vals['last_action_emp_id'] = vals.get('last_action_emp_id')
        return super(MedicalOrder, self).write(vals)

    def action_pricelist_approved(self):
        self.ensure_one()
        self.write({
            'pricelist_approved': True,
            'pricelist_approved_user_id': self.env.uid,
            'pricelist_approved_date': fields.Datetime.now()
        })

    def update_state_dates(self):
        now = fields.Datetime.now()
        date_list = ['date_arrived', 'date_in', 'date_out']
        for rec in self:
            vals = {}
            for afield in date_list:
                if not rec[afield]:
                    vals[afield] = now
            if vals:
                rec.write(vals)

    def unlink(self):
        # if self.mapped('line_ids.patient_move_line_ids'):
        raise UserError(_("Appointment cannot be deleted, You can cancel it."))
        # return super(MedicalOrder, self).unlink()

    @api.depends("state")
    def _compute_state_color(self):
        State = self.env['medical.state']
        for rec in self:
            rec.state_color = State.search([('name', '=', rec.state)], order='sequence desc', limit=1).s_color

    @api.depends('date_order', 'company_id', 'currency_id', 'company_id.currency_id')
    def _compute_currency_rate(self):
        Currency = self.env['res.currency']
        for order in self:
            company = order.company_id
            order.currency_rate = Currency._get_conversion_rate(
                company.currency_id, order.currency_id,
                company, order.date_order)

    @api.depends("line_ids", "line_ids.amount_paid", "net_total", "state")
    def _compute_amount_paid(self):
        for rec in self:
            amount_paid = due = 0
            if rec.state != 'cancel':
                amount_paid = sum(rec.line_ids.mapped('amount_paid'))
                due = rec.net_total - amount_paid
            rec.amount_paid = amount_paid
            rec.amount_due = due

    @api.depends("line_ids.duration", "start_time", "extra_time")
    def _compute_tot_duration(self):
        for order in self:
            if order.extra_time:
                total_duration = order.extra_time
            else:
                tot_dur = order.line_ids.mapped('duration')
                total_duration = sum(tot_dur) + order.extra_time
            order.update({
                'total_duration': total_duration,
                'end_time': order.start_time + timedelta(hours=total_duration)
            })

    @api.depends(
        'line_ids', 'line_ids.approved_price_unit', 'line_ids.payable_price_unit',
        'line_ids.ins_price_unit', 'line_ids.discount', 'line_ids.discount_fixed')
    def _compute_ins_amount(self):
        for order in self:
            tot_approved = tot_payable = tot_ins = 0
            for line in order.line_ids.filtered(lambda l: l.pricelist_item_id):
                tot_approved += (line.approved_price_unit * line.qty)
                tot_payable += (line.price_unit * line.qty)
                tot_ins += (line.ins_price_unit * line.qty)
            order.approved_tot_price = tot_approved
            order.payable_tot_price = tot_payable
            order.ins_tot_price = tot_ins

    @api.depends(
        'line_ids', 'line_ids.price_unit_orig', 'line_ids.product_id', 'line_ids.qty',
        'line_ids.price_unit', 'line_ids.discount', 'line_ids.discount_fixed')
    def _compute_order_total(self):
        for order in self:
            total = discount = net_total = 0
            orig_total = 0
            for line in order.line_ids:
                total += line.subtotal_wo_disc
                net_total += line.subtotal
                discount += line.subtotal_wo_disc - line.subtotal
                orig_total += line.price_unit_orig

            order.update({
                'orig_total': orig_total,
                'amount_total': total,
                'discount': discount,
                'net_total': net_total
            })

    def action_upd_insurance(self):
        tot_line_approved = self.approved_tot_price
        scheme = self.pricelist_id
        insurance_disc = scheme.insurance_disc
        tot_ins_vals = self.insurance_card_id.apply_insurance_total(tot_line_approved)
        payable_tot_price = tot_ins_vals.get('payable_tot_price')

        for line in self.line_ids.filtered('pricelist_item_id'):
            if line.ins_fixed:
                price_unit = line.price_unit
                ins_price_unit = line.approved_price_unit * (1 - insurance_disc / 100) - price_unit
                line.update({
                    'ins_price_unit': ins_price_unit,
                })
                continue

            ins_vals = line.pricelist_item_id.read([
                'ins_fixed',
                'insurance_disc', 'apply_ins_disc', 'patient_share', 'share_limit_type', 'patient_share_limit'])[0]
            ins_vals.pop('id')
            ins_vals = scheme.get_ins_values(line.approved_price_unit, ins_vals)

            price_unit = payable_tot_price * line.approved_price_unit / tot_line_approved
            ins_disc = line.approved_price_unit * insurance_disc / 100
            ins_price_unit = line.approved_price_unit - ins_disc - price_unit
            if line.ins_fixed:
                if line.apply_ins_disc == 'with':
                    ins_price_unit = ins_price_unit - price_unit
                else:
                    ins_price_unit = line.approved_price_unit * (1 - ins_vals['insurance_disc'] / 100)
                    ins_price_unit = ins_price_unit - price_unit
            line.update({
                'price_unit': price_unit,
                'ins_price_unit': ins_price_unit,
            })

    @api.depends('start_time')
    def _compute_last_order(self):
        for order in self:
            if order.id:
                order.last_order_id = self.search(
                    [('id', '!=', order.id), ('start_time', '<=', order.start_time), ('partner_id', '=', order.partner_id.id)],
                    limit=1).id
            else:
                order.last_order_id = False

    @api.depends('partner_id')
    def _is_first_appointment(self):
        for record in self.filtered(lambda o: not o.is_first):
            record.is_first = self.search_count([
                ('partner_id', '=', record.partner_id.id),
                ('partner_id.create_date', '>=', CONSIDERATION_DATE)
            ]) == 1

    @api.depends('handover_file_on', 'printed_file_on', 'date_arrived', 'date_in', 'date_out', 'state')
    def _compute_duration(self):
        for apmt in self.filtered('date_arrived'):
            dt_a = apmt.date_arrived
            if apmt.handover_file_on:
                dt_ho = apmt.handover_file_on
                apmt.handover_file_duration = str(dt_ho - dt_a)
            if apmt.printed_file_on:
                dt_prt = apmt.printed_file_on
                apmt.print_file_duration = str(dt_prt - dt_a)
            if apmt.date_in:
                apmt.duration_in_arrived = (apmt.date_in - dt_a).total_seconds() / 60
            if apmt.date_in and apmt.date_out:
                apmt.duration_out_in = (apmt.date_out - apmt.date_in).total_seconds() / 60

    @api.model
    def create(self, vals):
        config = MedicalConfig = self.env['medical.config']
        if vals.get('session_id') and not vals.get('config_id'):
            config = self.env['medical.session'].browse(vals['session_id']).config_id
            vals['config_id'] = config.id
        mc_id = vals.get('config_id')
        if mc_id:
            if not config:
                config = MedicalConfig.browse(mc_id)
            vals['name'] = config.sequence_id._next()
            if not vals.get('session_id'):
                vals['session_id'] = config.current_session_id.id
        return super(MedicalOrder, self).create(vals)

    def get_file_key(self):
        return self.config_id.depends_on or self.env.company.depends_on or 'file_no'

    def get_file_no(self):
        file_key = self.get_file_key()
        return self[file_key]

    def check_pricelist_approval(self):
        if self.filtered(lambda rec: rec.need_pricelist_approval and not rec.pricelist_approved):
            raise UserError(_('Pricelist is not approved by Management.'))

    def check_insurance_expiry(self, dt=False):
        if self.insurance_card_id and self.insurance_card_id.check_is_expired(dt):
            raise UserError(_(
                "'%s' insurance card is expired on %s.") % (
                self.insurance_card_id.name, str(self.insurance_card_id.expiry_date)))

    def action_validate(self):
        for rec in self.exists():
            # Update Invoice if already created
            rec.check_insurance_expiry()
            rec.create_patient_invoice()
            rec.patient_invoice_id.action_post()
            rec.write({'is_readonly': True})
        return True

    def action_cancel(self):
        self.ensure_one()
        if self.amount_paid > 0:
            raise UserError(_("Please Unreconcile or Cancel the linked payment(s) first."))
        if self.patient_invoice_id:
            # self.patient_invoice_id.button_draft()
            self.patient_invoice_id.button_cancel()

        if self.insurance_invoice_id:
            self.insurance_invoice_id.button_cancel()
            # self.insurance_invoice_id.button_draft()
        self.action_return_pickings()
        self.write({"state": 'cancel'})

    def action_return_pickings(self):
        pickings = self.consu_picking_id | self.picking_id
        order = self
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        for picking in pickings.filtered(lambda p: not p.is_med_returned):
            partner = self.partner_id
            moves = Move
            address = partner.address_get(['delivery']) or {}
            picking_type = picking.picking_type_id.return_picking_type_id
            if picking_type:
                location_id = picking_type.default_location_src_id.id
                destination_id = picking_type.default_location_dest_id.id
            else:
                picking_type = picking.picking_type_id
                location_id = picking.location_dest_id.id
                destination_id = picking.location_id.id

            message = _("""This return has been created from the medical order:
                <a href=# data-oe-model=medical.order data-oe-id=%d>%s</a>""") % (order.id, order.name)
            picking_vals = {
                'origin': order.name,
                'partner_id': address.get('delivery', False),
                'user_id': False,
                'date_done': fields.Datetime.now(),
                'picking_type_id': picking_type.id,
                'company_id': order.company_id.id,
                'move_type': 'direct',
                'note': order.note or "",
                'location_id': location_id,
                'location_dest_id': destination_id,
                'return_picking_id': picking.id,
                'medical_order_id': order.id,
                'company_code': order.company_code,
            }
            order_picking = Picking.create(picking_vals.copy())
            order_picking.sudo().message_post(body=message)
            self.sudo().message_post(body=message)

            for move in picking.move_ids_without_package:
                moves |= Move.create({
                    'name': move.name or move.product_id.name,
                    'product_uom': move.product_uom.id,
                    'picking_id': order_picking.id,
                    'picking_type_id': picking_type.id,
                    'product_id': move.product_id.id,
                    'product_uom_qty': abs(move.product_uom_qty),
                    'state': 'draft',
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                })
            if moves and order_picking:
                order._force_picking_done(order_picking)
                picking.write({'is_med_returned': True})

    def action_reset(self):
        self.ensure_one()
        if self.patient_invoice_id:
            self.patient_invoice_id.button_draft()
        if self.insurance_invoice_id:
            self.insurance_invoice_id.button_draft()
        self.action_return_pickings()
        self.write({"state": 'draft', 'is_readonly': False})

    def action_patient_invoice(self):
        self.ensure_one()
        if self.patient_invoice_id:
            raise UserError(_('Already Invoiced.'))

        if not self.line_ids:
            raise UserError(_("No Lines to Invoice."))

        if not self.config_id.invoice_journal_id:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        self.create_patient_invoice()
        return self.action_view_invoice()

    def action_view_invoice(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.patient_invoice_id.id
        action['context'] = {
            'default_type': 'out_invoice',
            'default_partner_id': self.partner_id.id,
            'default_invoice_origin': self.name,
        }
        return action

    def action_view_bill(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.insurance_invoice_id.id
        action['context'] = {
            'default_type': 'out_invoice',
            'default_partner_id': self.insurance_card_id.main_company_id.id,
            'default_invoice_origin': self.name,
        }
        return action

    def update_invoice(self, invoice):
        if invoice.state != 'draft':
            raise UserError(_("Invoice is not in draft state."))
        partner = self.partner_id
        dt = self.new_invoice_date or fields.Date.today()
        new_vals = {
            'invoice_date': dt,
            'invoice_date_due': dt,
            'insurance_card_id': self.insurance_card_id.id,
            'resource_id': self.resource_id.id,
            'currency_id': self.currency_id.id,
            'invoice_origin': self.name,
        }

        if invoice.is_insurance_invoice:
            partner = self.insurance_card_id.insurance_company_id

        if partner.id != invoice.partner_id.id:
            new_vals.update({
                'partner_id': partner.id,
                'fiscal_position_id': partner.property_account_position_id.id,
                'invoice_payment_term_id': partner.property_payment_term_id.id,
            })

        MoveLine = self.env['account.move.line']
        # inv_lines = invoice.invoice_line_ids
        new_inv_lines = [(5, 0, 0)]

        # tobe_remove = inv_lines.filtered(lambda l: not l.medical_order_line_id)
        # for l in tobe_remove:
        #     new_inv_lines.append((2, l.id, 0))

        for line in self.line_ids:
            price_unit = invoice.is_insurance_invoice and line.ins_price_unit or line.payable_price_unit
            # inv_line = inv_lines.filtered(lambda l: l.medical_order_line_id.id == line.id)

            if invoice.is_insurance_invoice and not line.ins_price_unit:
                continue

            inv_line_vals = self._prepare_invoice_line_vals(line, price_unit)
            inv_line_vals['move_id'] = invoice.id

            new_line = MoveLine.new(inv_line_vals)
            new_line.account_id = new_line._get_computed_account()

            new_line_values = new_line._convert_to_write(new_line._cache)
            # if inv_line:
            #     new_inv_lines.append((1, inv_line.id, new_line_values))
            # else:
            new_inv_lines.append((0, 0, new_line_values))

        new_vals.update({
            'invoice_line_ids': new_inv_lines,
        })
        invoice.write(new_vals)

    def create_patient_invoice(self):
        self.ensure_one()
        self.check_pricelist_approval()
        if self.patient_invoice_id:
            invoice = self.patient_invoice_id
            self.update_invoice(invoice)
        else:
            invoice_vals = self._prepare_patient_invoice_vals()
            invoice = self.env['account.move'].with_context(default_type='out_invoice').create(invoice_vals)
            self.write({'patient_invoice_id': invoice.id, 'state': 'invoiced'})

        lines = self.line_ids.filtered(lambda l: l.product_id.next_app_after)
        if lines and not self.next_appointment_id and not self.env.context.get('no_more_after_shot'):
            for line in lines:
                interval_days = line.product_id.next_app_after
                next_dt = self.start_time + timedelta(days=interval_days)
                new_app = self.with_context(no_more_after_shot=True).copy({'start_time': next_dt, 'is_followup': True})
                self.write({'next_appointment_id': new_app.id})
        return invoice

    def create_insurance_invoice(self):
        self.ensure_one()
        Model = self.env['account.move']
        if self.insurance_invoice_id:
            invoice = self.insurance_invoice_id
            self.update_invoice(invoice)
        else:
            invoice_vals = self._prepare_insurance_invoice_vals()
            if not invoice_vals:
                ctx = self.env.context
                if ctx.get('ignore_warning'):
                    return Model
                raise UserError(_("No lines for Insurance Invoice."))
            invoice = Model.with_context(default_type='out_invoice').create(invoice_vals)
        invoice.action_post()
        self.insurance_invoice_id = invoice.id
        return invoice

    def _prepare_invoice_line_vals(self, line, price=0):
        return {
            'medical_order_id': self.id,
            'medical_order_line_id': line.id,
            'product_id': line.product_id.id,
            'quantity': line.qty,
            'analytic_account_id': line.analytic_account_id.id or line.order_id.resource_id.analytic_account_id.id,
            'analytic_tag_ids': [(4, _id) for _id in line.analytic_tag_ids.ids],
            'product_uom_id': line.product_uom_id.id,
            'price_unit': price or line.payable_price_unit,
            'discount': line.discount,
            'discount_fixed': line.discount_fixed,
        }

    def _prepare_patient_invoice_vals(self):
        self.ensure_one()
        patient = self.partner_id

        lines = [self._prepare_invoice_line_vals(line) for line in self.line_ids]
        dt = self.new_invoice_date or fields.Date.today()
        invoice_vals = {
            'type': 'out_invoice',
            'narration': self.invoice_note,
            'medical_order_id': self.id,
            'is_patient_invoice': True,
            'invoice_date': dt,
            'invoice_date_due': dt,
            'insurance_card_id': self.insurance_card_id.id,
            'resource_id': self.resource_id.id,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.env.user.id,
            'partner_id': patient.id,
            'fiscal_position_id': patient.property_account_position_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': patient.property_payment_term_id.id,
            'incident_approval_no': self.ins_approval_no if self.ins_approval_no else '',
            'invoice_line_ids': [
                (0, 0, l)
                for l in lines
            ],
        }
        return invoice_vals

    def _prepare_insurance_invoice_vals(self):
        self.ensure_one()
        insurance_card = self.insurance_card_id
        insurance_company = insurance_card.insurance_company_id
        # ctx = self.env.context

        lines = []
        for l in self.line_ids.filtered('ins_price_unit'):
            lines.append((0, 0, {
                'product_id': l.product_id.id,
                'quantity': l.qty,
                'medical_order_id': self.id,
                'medical_order_line_id': l.id,
                'product_uom_id': l.product_uom_id.id,
                'analytic_account_id': l.analytic_account_id.id,
                'analytic_tag_ids': [(4, _id) for _id in l.analytic_tag_ids.ids],
                'price_unit': l.ins_price_unit,
                'discount': l.discount
            }))
        if not lines:
            return {}

        dt = self.new_invoice_date or fields.Date.today()
        inv_vals = {
            'type': 'out_invoice',
            'medical_order_id': self.id,
            'is_insurance_invoice': True,
            'insurance_card_id': insurance_card.id,
            'resource_id': self.resource_id.id,
            'currency_id': self.currency_id.id,
            'invoice_date': dt,
            'invoice_date_due': dt,
            'invoice_user_id': self.env.user.id,
            'partner_id': insurance_company.id,
            'fiscal_position_id': insurance_company.property_account_position_id.id,
            'invoice_origin': self.name,
            'ref_invoice_id': self.patient_invoice_id.id,
            'invoice_payment_term_id': insurance_company.property_payment_term_id.id,
            'incident_approval_no': self.ins_approval_no if self.ins_approval_no else '',
            'invoice_line_ids': lines,
        }
        return inv_vals

    def action_payment_wizard(self):
        if not self.patient_invoice_id:
            raise UserError(_('Please create the Invoice First.'))
        return self.patient_invoice_id.action_invoice_register_payment()

    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        # If no email is set on the user, the picking creation and validation will fail be cause of
        # the 'Unable to log message, please configure the sender's email address.' error.
        # We disable the tracking in this case.
        if not self.env.user.partner_id.email:
            Picking = Picking.with_context(tracking_disable=True)
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.line_ids.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                continue
            partner = order.partner_id
            address = partner.address_get(['delivery']) or {}
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = picking_type.default_location_src_id.id
            if partner:
                destination_id = partner.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _("""This transfer has been created from the medical session:
                    <a href=# data-oe-model=medical.order data-oe-id=%d>%s</a>""") % (order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'user_id': False,
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                    'medical_order_id': order.id,
                    'company_code': order.company_code,
                }
                pos_qty = any([x.qty > 0 for x in order.line_ids if x.product_id.type in ['product', 'consu']])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    if self.env.user.partner_id.email:
                        order_picking.message_post(body=message)
                    else:
                        order_picking.sudo().message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.line_ids if x.product_id.type in ['product', 'consu']])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    if self.env.user.partner_id.email:
                        return_picking.message_post(body=message)
                    else:
                        return_picking.message_post(body=message)

            for line in order.line_ids.filtered(
                    lambda l: l.product_id.type in ['product', 'consu'] and
                    not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                source_loc_id = location_id if line.qty >= 0 else destination_id
                dest_location_id = destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id
                moves |= Move.create({
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': source_loc_id,
                    'location_dest_id': dest_location_id,
                })

                # for cline in line.consumable_ids:
                #     product = cline.product_id
                #     moves |= Move.create({
                #         'name': product.name,
                #         'product_uom': product.uom_id.id,
                #         'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                #         'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                #         'product_id': product.id,
                #         'product_uom_qty': abs(cline.qty),
                #         'state': 'draft',
                #         'location_id': source_loc_id,
                #         'location_dest_id': dest_location_id,
                #     })

            # prefer associating the regular order picking, not the return
            order.write({'picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                moves._action_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

        return True

    def create_consumable_picking(self):
        Picking = self.env['stock.picking']
        # We disable the tracking in this case.
        if not self.env.user.partner_id.email:
            Picking = Picking.with_context(tracking_disable=True)
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            # if order.consu_picking_id and order.consu_picking_id.state == 'done' and not order.consu_picking_id.is_med_returned:
            #     return False
            consumable_lines = order.line_ids.mapped('consumable_ids').filtered(lambda l: l.product_id.type in ['product', 'consu'])
            if not consumable_lines:
                continue
            partner = order.partner_id
            address = partner.address_get(['delivery']) or {}
            resource = order.resource_id
            picking_type = order.config_id.cons_opr_type_id or resource.picking_type_id or order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = resource.medical_consumable_location_id.id
            med_config = order.config_on_validation or order.config_id
            if not location_id:
                location_id = med_config.location_id.id or picking_type.default_location_src_id.id
            if partner:
                destination_id = partner.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            destination_id = order.resource_id.destination_location_id.id or destination_id

            if picking_type:
                message = _("""This transfer has been created from the medical consumable:
                    <a href=# data-oe-model=medical.order data-oe-id=%d>%s</a>""") % (order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'user_id': False,
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                    'medical_order_id': order.id,
                    'company_code': order.company_code,
                }
                pos_qty = any([x.qty > 0 for x in consumable_lines])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    if self.env.user.partner_id.email:
                        order_picking.message_post(body=message)
                    else:
                        order_picking.sudo().message_post(body=message)
                neg_qty = any([x.qty < 0 for x in consumable_lines])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    if self.env.user.partner_id.email:
                        return_picking.message_post(body=message)
                    else:
                        return_picking.message_post(body=message)

            for line in consumable_lines.filtered(
                    lambda l: not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                source_loc_id = location_id if line.qty >= 0 else destination_id
                dest_location_id = destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id
                moves |= Move.create({
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': source_loc_id,
                    'location_dest_id': dest_location_id,
                    'medical_order_line_id': line.medical_order_line_id.id,
                })

            # prefer associating the regular order picking, not the return
            order.write({'consu_picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                moves._action_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

        return True

    def _force_picking_done(self, picking):
        """Force picking in order to be set as done."""
        self.ensure_one()
        picking.action_assign()
        wrong_lots = self.set_pack_operation_lot(picking)
        if not wrong_lots:
            picking.action_done()

    def set_pack_operation_lot(self, picking=None):
        """Set Serial/Lot number in pack operations to mark the pack operation done."""

        StockProductionLot = self.env['stock.production.lot']
        PosPackOperationLot = self.env['medical.pack.operation.lot']
        has_wrong_lots = False
        for order in self:
            for move in (picking or self.picking_id).move_lines:
                picking_type = (picking or self.picking_id).picking_type_id
                lots_necessary = True
                if picking_type:
                    lots_necessary = picking_type and picking_type.use_existing_lots
                qty_done = 0
                pack_lots = []
                pos_pack_lots = PosPackOperationLot.search([('order_id', '=', order.id), ('product_id', '=', move.product_id.id)])

                if pos_pack_lots and lots_necessary:
                    for pos_pack_lot in pos_pack_lots:
                        stock_production_lot = StockProductionLot.search([('name', '=', pos_pack_lot.lot_name), ('product_id', '=', move.product_id.id)])
                        if stock_production_lot:
                            # a serialnumber always has a quantity of 1 product, a lot number takes the full quantity of the order line
                            qty = 1.0
                            if stock_production_lot.product_id.tracking == 'lot':
                                qty = abs(pos_pack_lot.pos_order_line_id.qty)
                            qty_done += qty
                            pack_lots.append({'lot_id': stock_production_lot.id, 'qty': qty})
                        else:
                            has_wrong_lots = True
                elif move.product_id.tracking == 'none' or not lots_necessary:
                    qty_done = move.product_uom_qty
                else:
                    has_wrong_lots = True
                for pack_lot in pack_lots:
                    lot_id, qty = pack_lot['lot_id'], pack_lot['qty']
                    self.env['stock.move.line'].create({
                        'picking_id': move.picking_id.id,
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'qty_done': qty,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'lot_id': lot_id,
                    })
                if not pack_lots and not float_is_zero(qty_done, precision_rounding=move.product_uom.rounding):
                    if len(move._get_move_lines()) < 2:
                        move.quantity_done = qty_done
                    else:
                        move._set_quantity_done(qty_done)
        return has_wrong_lots


class MedicalOrderLine(models.Model):
    _name = 'medical.order.line'
    _description = 'Medical Order Line'
    _order = 'order_id desc'
    _rec_name = "product_id"

    order_id = fields.Many2one('medical.order', 'Appointment', index=True, ondelete='cascade')
    company_id = fields.Many2one(related="order_id.company_id")

    clinic_id = fields.Many2one(related="order_id.clinic_id", store=True)
    product_id = fields.Many2one('product.product', 'Product', required=True, index=True)
    qty = fields.Float('Quantity', required=True, default=1)
    product_type = fields.Selection(related="product_id.type", store=True)

    name = fields.Text("Description")

    price_unit_orig = fields.Float(digits=DP_MEDICAL, string='Actual Unit Price', help="Actual Product Unit Price")
    price_unit = fields.Float(digits=DP_MEDICAL, string='Unit Price', help="Unit Price")
    approved_price_unit = fields.Float(digits=DP_MEDICAL, string='Approved Unit Price', help="Insurance Approved Unit Price")
    payable_price_unit = fields.Float(
        digits=DP_MEDICAL, string="Patient Share",
        help="Payable Unit Price = Patient Share + (Unit Price - Approved Unit Price)",
        compute="_compute_all_price_unit")
    ins_price_unit = fields.Float(digits=DP_MEDICAL, string="Ins.Net Claim")

    product_uom_id = fields.Many2one('uom.uom', related='product_id.uom_id')
    # is_fixed_discount = fields.Boolean()
    discount = fields.Float(digits=DP_MEDICAL)
    discount_fixed = fields.Float(digits=DP_MEDICAL)
    # insurance_disc = fields.Float(digits=DP_MEDICAL, string=)
    subtotal = fields.Float(digits=DP_MEDICAL, string='Subtotal', compute='_compute_total', store=True)
    subtotal_wo_disc = fields.Float(digits=DP_MEDICAL, string='Subtotal w/o Discount', compute='_compute_total', store=True)
    # total = fields.Float(digits=DP_MEDICAL, string='Total', compute='_compute_total', store=True)
    duration = fields.Float()
    is_insurance_applicable = fields.Boolean(default=True)

    medical_waiting_list_id = fields.Many2one('app.waiting.list', string="Waiting List", copy=False)
    related_pkg_id = fields.Many2one(
        'customer.package', string='Related PKG', copy=False)
    pkg_index = fields.Integer("Package Sequence")
    # start_time = fields.Datetime(readonly=False)
    end_time = fields.Datetime(compute="_compute_end_time", store=True)
    # consumable_ids = fields.Many2many(
    #     'product.product', 'pos_order_line_product_consumable_rel', 'parent_product_id', 'child_product_id',
    #     string='Consumables', domain=[('is_medical_consumable', '=', True)])
    consumable_ids = fields.One2many("medical.order.line.consumable", "medical_order_line_id", string='Consumables')
    note = fields.Char('Note', copy=False)
    session_count = fields.Integer(string='Sessions', default=1)

    # Insurance + Pricelist
    pricelist_item_id = fields.Many2one("product.pricelist.item", "Pricelist Item")
    patient_share = fields.Float(digits=DP_MEDICAL, string="Deductible Amount", help="If value <= 0 then it will be ignored.")
    share_limit_type = fields.Selection([
        ('min', 'Min'), ('max', 'Max')], string="Share Limit Type")
    ins_fixed = fields.Float(digits=DP_MEDICAL, string="Fixed Ins. Amount")
    patient_share_limit = fields.Float(digits=DP_MEDICAL, string="Patient Share Limit", help="If value <= 0 then it will be ignored.")
    insurance_disc = fields.Float(digits=DP_MEDICAL, string="Ins.Company Discount")
    apply_ins_disc = fields.Selection(
        APPLY_INS_DISC_SELECTION, default='after',
        string=APPLY_INS_DISC_STRING,
        help=APPLY_INS_DISC_HELP)

    # Related From Order
    currency_id = fields.Many2one(related="order_id.currency_id", store=True, readonly=True)
    partner_id = fields.Many2one(related="order_id.partner_id", store=True, readonly=True)
    file_no = fields.Char(related="partner_id.file_no", store=True, readonly=True)
    file_no2 = fields.Char(related="partner_id.file_no2", store=True, readonly=True)
    civil_code = fields.Char(related="partner_id.civil_code", store=True, readonly=True)
    start_time = fields.Datetime(related="order_id.start_time", store=True, readonly=True)
    # end_time = fields.Datetime(related="order_id.end_time", store=True, readonly=True)
    total_duration = fields.Float(related="order_id.total_duration", store=True, readonly=True)
    resource_id = fields.Many2one(related="order_id.resource_id", store=True, readonly=True)
    state = fields.Selection(related="order_id.state", store=True, readonly=True)
    session_id = fields.Many2one(related="order_id.session_id", store=True, readonly=True)
    config_id = fields.Many2one(related="order_id.config_id", store=True, readonly=True)
    insurance_card_id = fields.Many2one(related="order_id.insurance_card_id", store=True, readonly=True)
    insurance_company_id = fields.Many2one(related="insurance_card_id.insurance_company_id", store=True, readonly=True)
    user_id = fields.Many2one(related="order_id.user_id", store=True, readonly=True)
    pricelist_id = fields.Many2one(related="order_id.pricelist_id", store=True, readonly=True)
    patient_invoice_id = fields.Many2one(related="order_id.patient_invoice_id", store=True)
    insurance_invoice_id = fields.Many2one(related="order_id.insurance_invoice_id", store=True)
    ins_invoice_date = fields.Date(related="insurance_invoice_id.invoice_date", store=True, string="Ins.Invoice Date")

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=True)
    tax_ids_after_fiscal_position = fields.Many2many('account.tax', compute='_get_tax_ids_after_fiscal_position', string='Taxes to Apply')

    patient_move_line_ids = fields.One2many(
        "account.move.line", "medical_order_line_id",
        domain=[('move_id.is_patient_invoice', '=', True)], string="Patient Invoice Lines")
    ins_move_line_ids = fields.One2many(
        "account.move.line", "medical_order_line_id",
        domain=[('move_id.is_insurance_invoice', '=', True)], string="Insurance Invoice Lines")

    # payment_ids = fields.Many2many("account.payment", string="Appointment Line Payments")
    amount_paid = fields.Float(digits=DP_MEDICAL, string="Paid", copy=False)
    amount_due = fields.Float(string="Amount Due", compute="_compute_amount_paid", digits=DP_MEDICAL, store=True)

    pkg_amount = fields.Float("Package Amount", compute="_compute_pkg_amount", store=True)

    @api.model
    def create(self, vals):
        if vals.get('price_unit'):
            if not vals.get('approved_price_unit'):
                vals['approved_price_unit'] = vals['price_unit']
            if not vals.get('price_unit_orig'):
                vals['price_unit_orig'] = vals['price_unit']
        record = super(MedicalOrderLine, self).create(vals)
        return record

    @api.depends('related_pkg_id', 'qty')
    def _compute_pkg_amount(self):
        for rec in self:
            pkg_amount = 0
            pkg = rec.related_pkg_id
            if pkg:
                pkg_amount = rec.currency_id.round(pkg.session_price / pkg.session_total) * rec.qty
            rec.pkg_amount = pkg_amount

    @api.depends('patient_move_line_ids.amount_paid', 'subtotal')
    def _compute_amount_paid(self):
        for line in self:
            # all_payments = line.order_id.payment_ids
            # all_move_lines = all_payments.mapped('paid_move_line_ids')
            # cur_line_payments = all_move_lines.filtered(lambda r: r.medical_order_line_id.id == line.id)
            # amount_paid = sum(line.patient_move_line_ids.mapped('amount_paid'))
            # print ('_ _compute_amount_paid : ', line.amount_paid, amount_paid)
            # line.amount_paid = amount_paid
            line.amount_due = line.subtotal - line.amount_paid

    @api.constrains('analytic_account_id', 'analytic_tag_ids')
    def _check_analytic_either(self):
        for rec in self:
            if rec.analytic_account_id and rec.analytic_tag_ids:
                raise UserError(_('Either Analytic Account or Tags can be linked with the service line "%s"') % (rec.name))

    @api.depends('order_id', 'order_id.fiscal_position_id')
    def _get_tax_ids_after_fiscal_position(self):
        for line in self:
            line.tax_ids_after_fiscal_position = line.order_id.fiscal_position_id.map_tax(line.tax_ids, line.product_id, line.order_id.partner_id)

    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if product.description_sale:
            values.append(product.description_sale)
        return '\n'.join(values)

    @api.onchange('product_id', 'is_insurance_applicable', 'qty')
    def _onchange_product_id(self):
        product = self.product_id
        order = self.order_id
        # price = product.lst_price

        result = {
            'name': self._get_computed_name(),
            'analytic_account_id': order.resource_id.analytic_account_id.id,
            'analytic_tag_ids': product.analytic_tag_ids.ids,
            'duration': product.duration,
        }

        # result = {
        #     'price_unit_orig': price,
        #     'price_unit': price,
        #     'approved_price_unit': price,
        #     'duration': product.duration,
        #     'description': self._get_computed_name(),
        #     'analytic_account_id': order.resource_id.analytic_account_id.id,
        #     'analytic_tag_ids': product.analytic_tag_ids.ids,
        #     'ins_price_unit': 0,
        # }
        # insurance_card = self.insurance_card_id
        # if product and self.is_insurance_applicable and insurance_card:
        #     price = product.with_context(
        #         lang=self.partner_id.lang,
        #         partner=self.partner_id,
        #         quantity=self.qty,
        #         date=order.date_order,
        #         pricelist=self.pricelist_id.id,
        #         uom=self.product_uom_id.id
        #     ).price
        #     result.update({
        #         'price_unit_orig': price,
        #         'price_unit': price,
        #         'approved_price_unit': price,
        #     })
        #     if self.is_insurance_applicable and insurance_card:
        #         price_result = insurance_card.apply_insurance_rule(
        #             self.product_id, self.qty)
        #         result.update(price_result)

        # if not self.is_insurance_applicable and self.pricelist_item_id:
        #     result.update({'pricelist_item_id': False})

        ins_result = self.insurance_card_id._check_insurance_wrapper(
            self.product_id, self.qty, 0, self.is_insurance_applicable)
        result.update(ins_result)

        self.update(result)

    @api.onchange('approved_price_unit')
    def _onchange_approved_price_unit(self):
        insurance_card = self.insurance_card_id
        if self.product_id and self.is_insurance_applicable and insurance_card:
            result = insurance_card.apply_insurance_rule(
                self.product_id, self.qty, self.approved_price_unit)
            self.update(result)

    @api.depends("price_unit", "approved_price_unit", "is_insurance_applicable", "price_unit_orig")
    def _compute_all_price_unit(self):
        for rec in self:
            pay_price = rec.price_unit_orig
            if rec.is_insurance_applicable:
                pay_price = rec.price_unit + (pay_price - rec.approved_price_unit)
            rec.payable_price_unit = pay_price

    @api.depends('product_id', 'qty', 'discount', 'discount_fixed', 'payable_price_unit')
    def _compute_total(self):
        for line in self:
            subtotal_wo_disc = line.qty * line.payable_price_unit
            subtotal = subtotal_wo_disc
            if line.discount:
                subtotal = subtotal_wo_disc * (1 - line.discount / 100)
            elif line.discount_fixed:
                subtotal = subtotal_wo_disc - line.discount_fixed

            line.update({
                'subtotal_wo_disc': subtotal_wo_disc,
                'subtotal': subtotal
            })

    @api.depends('duration')
    def _compute_end_time(self):
        for line in self:
            end_time = False
            if line.start_time:
                end_time = line.start_time + timedelta(hours=line.duration)
            line.end_time = end_time


class MedicalOrderLineLot(models.Model):
    _name = "medical.pack.operation.lot"
    _description = "Specify product lot/serial number in medical order line"
    _rec_name = "lot_name"

    medical_order_line_id = fields.Many2one('medical.order.line')
    order_id = fields.Many2one('medical.order', related="medical_order_line_id.order_id", readonly=False)
    lot_name = fields.Char('Lot Name')
    product_id = fields.Many2one('product.product', related='medical_order_line_id.product_id', readonly=False)


class MedicalOrderLineConsumable(models.Model):
    _name = "medical.order.line.consumable"
    _description = "Medical Order Line Consumable"

    medical_order_line_id = fields.Many2one("medical.order.line")
    product_id = fields.Many2one("product.product", domain=[("is_medical_consumable", "=", True)])
    qty = fields.Float()
    company_id = fields.Many2one(related="medical_order_line_id.company_id")
