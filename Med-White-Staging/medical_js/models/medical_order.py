# -*- coding: utf-8 -*-
import logging
# import psycopg2
import json
from functools import partial

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.medical_js.controllers.medical import ORDER_LINE_FIELDS, PARTNER_FIELDS, ADDRESS_FIELDS
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MedicalResource(models.Model):
    _inherit = 'medical.resource'

    partner_id = fields.Many2one('res.partner', string="Partner")
    clinic_name = fields.Char("Clinic")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.clinic_name:
                name = "%s, %s" % (rec.clinic_name, name)
            result.append((rec.id, name))
        return result

    @api.model
    def add_new_resource(self, vals):
        rec = self.create(vals)
        return rec.read([
            'name', 'note', 'working_hour_id', 'hr_staff_id', 'sequence', 'analytic_account_id', 'group_id'])[0]


class MedicalOrder(models.Model):
    _inherit = 'medical.order'

    ui_reference = fields.Char("UI Reference", readonly=True)
    sequence_number = fields.Integer("Sequence Number", default=1)
    active = fields.Boolean(default=True)
    sequence_no = fields.Integer()
    invoice_state = fields.Selection(related="patient_invoice_id.state", store=True, string="Invoice State")
    invoice_date = fields.Date(related="patient_invoice_id.invoice_date", store=True, string="Invoice Date")
    is_multi_order = fields.Boolean("Is Multi Order ?", compute="_compute_is_multi_app")
    prepaid_card_id = fields.Many2one("partner.prepaid.card", string="Prepaid Card", domain="[('partner_id', '=', partner_id)]")
    email = fields.Char(related="partner_id.email")
    passport_no = fields.Char(related="partner_id.passport_no")

    is_direct_sale = fields.Boolean("Is Direct Sales ?", compute="_compute_is_direct_sale", store=True)
    payment_history_ids = fields.One2many('aml.payment.history', 'medical_order_id', string="Payments")

    disc_reason_id = fields.Many2one("discount.reason", string="Discount Reason")
    config_on_validation = fields.Many2one('medical.config', string="Scheduler on Validation", tracking=True)

    def write(self, vals):
        if vals.get('state') and vals['state'] == 'arrived':
            self.check_on_arrive_fields()
        return super().write(vals)

    def check_on_arrive_fields(self):
        for rec in self:
            if rec.config_id.req_patient_civil_on_arrive and not rec.partner_id.civil_code:
                raise UserError(_("Civil ID is Required"))
            if rec.config_id.req_patient_file_on_arrive and not rec.get_file_no():
                raise UserError(_("File No/File No2 is Required"))
            if rec.config_id.req_patient_gender_on_arrive and not rec.partner_id.gender:
                raise UserError(_("Gender is Required"))
            if rec.config_id.req_patient_fulladdress_on_arrive and not rec.partner_id.street2:
                raise UserError(_("Full Address Line is Required"))
            if rec.config_id.req_patient_bday_on_arrive and not rec.partner_id.birthday:
                raise UserError(_("Birth Date is Required"))

    @api.depends('resource_id', 'line_ids.multi_resource_id')
    def _compute_is_multi_app(self):
        for rec in self:
            rec.is_multi_order = len(
                rec.line_ids.filtered(
                    lambda l: l.qty > 0 and l.multi_resource_id and l.multi_resource_id.id != rec.resource_id.id).ids) > 0

    @api.depends('line_ids', 'line_ids.product_id', 'line_ids.product_id.type')
    def _compute_is_direct_sale(self):
        for rec in self:
            rec.is_direct_sale = not bool(rec.line_ids.filtered(lambda line: line.product_id.type == 'service'))

    @api.model
    def next_sequence_no(self):
        return int(self.env['ir.sequence'].next_by_code('appointment.seq.per.day'))

    def _prepare_invoice_line_vals(self, line, price=0):
        vals = super(MedicalOrder, self)._prepare_invoice_line_vals(line, price=price)
        vals['employee_id'] = line.employee_id.id
        return vals

    def action_validate(self):
        super(MedicalOrder, self).action_validate()
        self.exists().create_package()
        return True

    def create_package(self):
        packages = Package = self.env['customer.package']
        for order in self:
            lines = order.line_ids.filtered(lambda l: l.session_count > 1)
            # If Package is Not Linked Create a New Package
            for line in lines.filtered(lambda l: not l.related_pkg_id):
                product = line.product_id
                running_package = Package.create({
                    'name': product.display_name,
                    'product_id': product.id,
                    'invoice_id': order.patient_invoice_id.id,
                    'partner_id': order.partner_id.id,
                    'session_total': product.session_count,
                    'duration': line.duration,
                    'session_done': 1,
                    'medical_order_id': order.id,
                    'session_price': line.subtotal,
                    # 'medical_order_line_ids': [(4, line.id)],
                })
                line.pkg_index = 1
                packages += running_package

            for line in lines.filtered(lambda l: l.related_pkg_id):
                line.pkg_index += 1
        return packages

    def update_appointment_resource(self, data):
        start_time = data.get('start_time')
        vals = {}
        line_vals = {}
        if start_time:
            vals['start_time'] = start_time
            line_vals['multi_start_time'] = start_time
        if data.get('resource_id'):
            vals['resource_id'] = data['resource_id']
            emp = self.env['medical.resource'].browse(data['resource_id']).hr_staff_id
            line_vals.update({
                'multi_resource_id': data['resource_id'],
                'employee_id': emp.id,
            })
        if vals:
            self.write(vals)
        if data.get('old_resource_id') and line_vals:
            res_id = data['old_resource_id']
            lines = self.line_ids.filtered(
                lambda line: line.multi_resource_id.id == res_id)
            if lines:
                lines.write(line_vals)

    @api.model
    def get_uninvoiced_orders(self, partner_id, exclude_order_ids=[]):
        domain = [
            ('patient_invoice_id', '=', False), ('partner_id', '=', partner_id),
            ('state', 'not in', ['cancel'])
        ]
        if exclude_order_ids:
            domain += [('id', 'not in', exclude_order_ids)]
        orders = self.env['medical.order'].search(domain, order="start_time desc")
        data_orders = []
        for order in orders:
            order_data = order.read(['name', 'net_total', 'state'])[0]
            order_data.update({
                "orderlines": order.line_ids.read(['product_id', 'subtotal'])
            })

            data_orders.append(order_data)
        return data_orders

    def get_invoice_data(self, order_id=None, invoice_id=None):
        invoice = Invoice = self.env['account.move']
        order = False
        if order_id:
            order = self.with_user(SUPERUSER_ID).browse(order_id)
            invoice = order.patient_invoice_id
        if invoice_id:
            invoice = Invoice.with_user(SUPERUSER_ID).browse(invoice_id)
            order = invoice.medical_order_id
        final_data = {
            'state': 'draft',
        }
        if invoice:
            inv_data = invoice.read([
                'name', 'partner_id', 'resource_id', 'state', 'payment_comment', 'ref_invoice_id',
                'invoice_payment_state', 'insurance_card_id', 'amount_total', 'amount_residual',
                'medical_order_id'])[0]
            final_data.update({'invoice_data': inv_data})

            inv_lines = []
            for line in invoice.invoice_line_ids:
                line_data = line.read([
                    'product_id', 'quantity', "session_count",
                    'product_uom_id', 'price_unit', 'discount', 'discount_fixed', 'medical_order_id',
                    'employee_id',
                    'price_subtotal', 'analytic_account_id', 'analytic_tag_ids',
                    'payment_ids', 'amount_paid', 'amount_pay_status', 'medical_order_line_id',
                    'refund_amount'])[0]

                med_line = line.medical_order_line_id
                line_data.update({
                    'medical_line': med_line and med_line.read(ORDER_LINE_FIELDS)[0] or {}
                })

                inv_lines.append(line_data)

            insurance_data = {}
            if invoice.insurance_card_id:
                insurance_data = invoice.insurance_card_id.read(['name', 'pricelist_id', 'insurance_company_id', 'main_company_id'])[0]
            final_data.update({
                'order_lines': inv_lines,
                'insurance_data': insurance_data,
                'has_insurance': invoice.insurance_card_id and True or False,
                'outstanding': json.loads(invoice.invoice_outstanding_credits_debits_widget or {}),
                'payments': json.loads(invoice.invoice_payments_widget or {}),
                # 'insurance_invoice_ids': [],
                'analytic_tag_ids': {tag.id: tag.name for tag in invoice.invoice_line_ids.mapped('analytic_tag_ids')},
            })

        elif order:
            final_data.update(order.read(
                ['resource_id', 'name', 'partner_id', 'note', 'invoice_note', 'is_followup'])[0])
            final_data.pop('id')
            order_lines = []
            for line in order.line_ids:
                line_data = line.read(ORDER_LINE_FIELDS)[0]
                order_lines.append(line_data)
            final_data.update({
                'name': _('INVOICE'),
                'order_lines': order_lines,
            })

        if order:
            refund_invoices = []
            out_refund_moves = Invoice.search([('medical_order_id', '=', order.id), ('type', '=', 'out_refund'), ('state', '=', 'posted')])
            if out_refund_moves:
                for inv in out_refund_moves:
                    refund_inv_data = inv.read([
                        'name', 'state', 'invoice_date',
                        'invoice_payment_state', 'amount_total'])[0]

                    refund_inv_data.update({
                        'invoice_lines': inv.invoice_line_ids.read(['name', 'product_id', 'price_subtotal'])
                    })

                    refund_invoices.append(refund_inv_data)

            final_data.update({
                'medical_order_id': order.id,
                'paymentlines': order.get_payment_details(),
                'discount': order.discount,
                'ins_tot_price': order.ins_tot_price,
                'refund_invoices': refund_invoices
            })
            if order.partner_id:
                partner = order.partner_id
                final_data.update({
                    'file_no': partner.file_no,
                    'file_no2': partner.file_no2,
                    'partner': partner and partner.read(PARTNER_FIELDS + ADDRESS_FIELDS + ['ins_running_card_ids'])[0],
                })
        return final_data

    # def check_documents(self):
    #     self.ensure_one()
    #     if not self.partner_id.file_no:
    #         raise UserError(_('File No. required to generate the Invoice.'))
    #         return False
    #     if self.is_traveller_swab and self.is_app_pcr and self.partner_id:
    #         document_type_ids = self.partner_id.mapped('medical_attachment_ids.attachment_type_id').filtered(lambda t: t.attachment_type == 'passport')
    #         if not document_type_ids:
    #             raise UserError(_('Please Upload Passport of Patient'))
    #             return False
    #     return True

    def action_create_invoice_wrapper(self):
        self.ensure_one()
        if self._context.get('config_on_validation') and self._context['config_on_validation']:
            self.write({'config_on_validation': self._context['config_on_validation']})
        if not self.partner_id.file_no:
            raise UserError(_('File No. required to generate the Invoice.'))
        # self.action_validate()
        self.create_patient_invoice()
        self.write({'is_readonly': True})
        # return {
        #     'is_readonly': self.is_readonly,
        #     'invoice_number': self.invoice_number,
        # }
        if self.config_id.inv_validation_on == "app":
            return self.action_validate_wrapper()
        return self.get_invoice_data(order_id=self.id)

    def update_inv_inputs(self, inv_inputs):
        return

    def action_validate_wrapper(self, inv_inputs=None):
        inv_inputs = inv_inputs or {}
        self.ensure_one()
        if inv_inputs:
            self.update_inv_inputs(inv_inputs)
        self.action_validate()
        return self.get_invoice_data(order_id=self.id)

    def action_cancel_wrapper(self):
        self.ensure_one()
        self.action_cancel()
        return {
            'is_readonly': self.is_readonly,
            'invoice_number': self.invoice_number,
        }

    def action_reset_wrapper(self):
        self.ensure_one()
        self.action_reset()
        return {
            'is_readonly': self.is_readonly,
            'invoice_number': self.invoice_number,
        }

    @api.model
    def create_from_ui(self, orders):
        order_ids = []
        for order in orders:
            existing_order = self.search([
                '|', '|',
                ('id', '=', order['data'].get('server_id')),
                ('ui_reference', '=', order['data']['name']),
                ('name', '=', order['data']['name'])], limit=1)
            if (existing_order and (not existing_order.patient_invoice_id or existing_order.patient_invoice_id.state == 'draft')) or not existing_order:
                order_ids.append(self._process_order(order, existing_order))
            else:
                logging.info(
                    "____ Create/Update Appointment Fail Exists: %s - %s - %s",
                    existing_order, existing_order.patient_invoice_id, existing_order.state)

        result = self.search_read(
            domain=[('id', 'in', order_ids)], fields=['id', 'ui_reference'])
        logging.info("____ %s Appointment : %s By %s-%s", existing_order and 'Updated' or 'Created', result, self.env.uid, self.env.user.name)
        return result

    def _get_valid_session(self, order):
        MedicalSession = self.env['medical.session']
        closed_session = MedicalSession.browse(order['medical_session_id'])

        _logger.warning('session %s (ID: %s) was closed but received order %s (total: %s) belonging to it',
                        closed_session.name,
                        closed_session.id,
                        order['name'])
        rescue_session = MedicalSession.search([
            ('state', 'not in', ('closed', 'closing_control')),
            ('rescue', '=', True),
            ('config_id', '=', closed_session.config_id.id),
        ], limit=1)
        if rescue_session:
            _logger.warning('reusing recovery session %s for saving order %s', rescue_session.name, order['name'])
            return rescue_session

        _logger.warning('attempting to create recovery session for saving order %s', order['name'])
        new_session = MedicalSession.create({
            'config_id': closed_session.config_id.id,
            'name': _('(RESCUE FOR %(session)s)') % {'session': closed_session.name},
            'rescue': True,  # avoid conflict with live sessions
        })
        # bypass opening_control (necessary when using cash control)
        new_session.action_pos_session_open()

        return new_session

    @api.model
    def _process_order(self, order, existing_order):
        order = order['data']
        pos_session = self.env['medical.session'].browse(order['medical_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['medical_session_id'] = self._get_valid_session(order).id

        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))

            if (order.get('waiting_list_id')) and pos_order.waiting_list_id.state != 'done':
                pos_order.waiting_list_id.mark_as_done()

            pos_order.session_id.add_sequence_number()
        else:
            pos_order = existing_order
            pos_order.line_ids.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        return pos_order.id

    @api.model
    def _order_fields(self, ui_order, existing_order=None):
        process_line = partial(self.env['medical.order.line']._order_line_fields, session_id=ui_order['medical_session_id'])
        order_vals = {}
        if not existing_order:
            order_vals.update({
                'session_id':   ui_order['medical_session_id'],
                'ui_reference': ui_order['name'],
                'sequence_number': ui_order['sequence_number'],
                'sequence_no': ui_order.get('sequence_no', self.next_sequence_no()),
            })
        order_vals.update({
            'line_ids':        [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'partner_id':   ui_order['partner_id'] or False,
            'fiscal_position_id': ui_order['fiscal_position_id'],
            'pricelist_id': ui_order.get('pricelist_id'),
            'need_pricelist_approval': ui_order.get('need_pricelist_approval'),
            'resource_id': ui_order.get('resource_id'),
            'start_time': ui_order.get('start_time'),
            'employee_id': ui_order.get('employee_id'),
            'clinic_id': ui_order.get('clinic_id'),
            'insurance_card_id': ui_order.get('insurance_card_id'),
            "ins_approval_no": ui_order.get('ins_approval_no'),
            "ins_ticket_no": ui_order.get('ins_ticket_no'),
            "ins_ref": ui_order.get('ins_ref'),
            "ins_member": ui_order.get('ins_member'),
            "visit_type": ui_order.get('visit_type') or None,
            "is_multi_order": ui_order.get('is_multi_order') or None,
            "waiting_list_id": ui_order.get('waiting_list_id') or None,
            'disc_reason_id': ui_order.get('disc_reason_id') or None,
            # 'orig_order_id': ui_order.get('orig_order_id'),
            # 'invoice_note': ui_order.get('invoice_note'),
            # 'is_followup': ui_order.get('is_followup'),

            'prepaid_card_id': ui_order.get('prepaid_card_id'),
            'visit_opt_id': ui_order.get('visit_opt_id'),
        })
        return order_vals

    def reset_sequence_afterwards_appointments(self):
        self.ensure_one()
        start_time_str = fields.Date.to_string(self.start_time)
        orders = self.search([
                ('start_time', '>', start_time_str),
                ('end_time', '<=', start_time_str)
            ], order="start_time")
        for order in orders:
            next_seq_no = self.next_sequence_no()
            while next_seq_no <= self.sequence_no:
                next_seq_no = self.next_sequence_no()
            order.sequence_no = next_seq_no
        return True

    def prepare_payment_line(self, def_vals, cmp_currency, line):
        journal_id = int(line.get('journal_id'))
        journal = self.env['account.journal'].browse(journal_id)
        amount = line.get('amount')
        partner_id = self.partner_id.id or line.get("partner_id")
        communication = line.get("communication") or self.name

        vals = dict(def_vals, **{
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_date': fields.Date.today(),
            'partner_id': partner_id,
            'amount': amount,
            'journal_id': journal_id,
            'prepaid_card_id': line.get('prepaid_card_id'),
            'medical_order_id': self.id or (line.get('medical_order_id') and int(line['medical_order_id'])),
            'communication': communication,
            'currency_id': cmp_currency.id,
            'session_id': line.get('session_id'),
            'branch_id': line.get('branch_id') or self._context.get('deafult_branch_id') or self.clinic_id.id or None,
            'payment_method_id': journal.inbound_payment_method_ids and journal.inbound_payment_method_ids[0].id,
        })
        if self.patient_invoice_id.id:
            vals.update({
                'invoice_ids': [(4, self.patient_invoice_id.id)]
            })
        if journal.currency_id:
            vals.update({
                'currency_id': journal.currency_id.id
            })
        return vals

    def register_payment_from_ui(self, payment_lines,  payment_comment='', invoice_lines=[]):
        # self.ensure_one()
        # pos_order = self.pos_order_id
        # if not pos_order and self.env.context.get('pos_order_id'):
        #     pos_order = self.env['pos.order'].browse(self.env.context['pos_order_id'])
        # if pos_order:
        #     pos_order.order_payment(payment_lines)

        payments = Payment = self.env['account.payment']
        cmp_currency = self.env.user.company_id.currency_id
        ctx = dict(self.env.context, **{
            'default_payment_type': 'inbound',
            'default_partner_type': 'customer',
            'active_ids': self.ids,
        })
        def_vals = Payment.with_context(ctx).default_get(['payment_method_id', 'payment_type', 'payment_method_code'])
        for line in payment_lines or []:
            vals = self.prepare_payment_line(def_vals, cmp_currency, line)
            payments += Payment.with_context(ctx).create(vals)
        payments.post()

        lines = self.env['account.move.line']
        if invoice_lines:
            lines = payments.update_aml_amount_paid(invoice_lines)

        if self.id and self.amount_due == 0:
            self.write({'state': 'paid'})
            self.create_consumable_picking()

        res_vals = {
            'state': self.state,
            'paymentlines': self.get_payment_details(),
            'credit': self.partner_id.credit,
            'invoice_payment_state': self.patient_invoice_id.invoice_payment_state,
            'invoice_lines': lines.read(['amount_paid', 'amount_pay_status'])
        }
        return res_vals

    def get_payment_details(self):
        result = []
        for payment in self.payment_ids.filtered(lambda p: p.state in ['posted', 'reconciled']):
            currency = payment.currency_id
            move_ids = payment.move_line_ids.mapped('move_id.id')
            amount = payment.amount
            if payment.payment_type == 'outbound':
                amount = amount * -1
            result.append({
                'journal_name': payment.journal_id.name,
                'amount': amount,
                'currency': currency.symbol,
                'id': payment.id,
                'position': currency.position,
                'digits': [69, currency.decimal_places],
                'payment_date': payment.payment_date,
                'move_id': move_ids and move_ids[0] or False,
                'aml_ids': payment.paid_move_line_ids.ids,
            })
        return result

    def log_time(self, field_name):
        dt = fields.Datetime.now()
        self.write({field_name: dt})
        return dt


class MedicalOrderLine(models.Model):
    _inherit = 'medical.order.line'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    is_tip = fields.Boolean("Is Tip ?")
    multi_resource_id = fields.Many2one('medical.resource', string="Resource")
    multi_start_time = fields.Datetime(string="Multi Start Time")
    line_type = fields.Char(compute="_compute_line_type", store=True)
    invoice_id = fields.Many2one(related="order_id.patient_invoice_id", store=True, string="Invoice")
    invoice_date = fields.Date(related="order_id.invoice_date", store=True, string="Invoice Date")
    invoice_state = fields.Selection(related="order_id.invoice_state", store=True, string="Invoice State")

    @api.depends("product_id", "related_pkg_id", "is_tip", "product_type")
    def _compute_line_type(self):
        for line in self:
            ltype = 'service'
            if line.is_tip or line.config_id.tip_prod_id.id == line.product_id.id:
                ltype = 'tip'
            elif line.related_pkg_id or line.session_count > 1:
                ltype = 'package'
            elif line.product_type != 'service':
                ltype = 'product'
            line.line_type = ltype

    def _order_line_fields(self, line, session_id=None):
        if line and 'tax_ids' not in line[2]:
            product = self.env['product.product'].browse(line[2]['product_id'])
            line[2]['tax_ids'] = [(6, 0, [x.id for x in product.taxes_id])]
        # Clean up fields sent by the JS
        line = [
            line[0], line[1], {k: v for k, v in line[2].items() if k in self._fields}
        ]
        return line

    def update_appointment_resource(self, data):
        start_time = data.get('start_time')
        vals = {}
        if start_time:
            vals['multi_start_time'] = start_time
        if data.get('resource_id'):
            emp = self.env['medical.resource'].browse(data['resource_id']).hr_staff_id
            vals.update({
                'multi_resource_id': data['resource_id'],
                'employee_id': emp.id
            })
        if vals:
            self.write(vals)

    def update_consumables(self, vals):
        if vals.get('consumable_ids'):
            prod_qty_req = {}
            for line in vals.get('consumable_ids'):
                if len(line) > 2 and line[0] < 2:
                    pid = line[2]['product_id']
                    prod_qty_req.setdefault(pid, 0)
                    prod_qty_req[pid] += line[2]['qty']
            if prod_qty_req:
                prod_ids = list(prod_qty_req.keys())
                prod_data = self.get_consumable_stock(self, extra_domain=[('id', 'in', prod_ids)])
                not_available = []
                if not prod_data:
                    raise UserError(_("Stock not available."))
                for prod in prod_data:
                    if prod['id'] not in prod_ids or prod['qty_available'] < prod_qty_req[prod['id']]:
                        not_available.append(prod['display_name'])
                if not_available:
                    raise UserError(_("Stock is not available for below products.\n%s") % ('\n'.join(not_available)))
        self.write(vals)
        return self.consumable_ids.ids

    def get_consumable_stock(self, medical_line, extra_domain=[]):
        order = medical_line.order_id
        location = (medical_line.multi_resource_id or order.resource_id).medical_consumable_location_id or order.config_id.location_id
        ctx = {
            'location': location.id,
        }
        products_data = []
        Product = self.env['product.product'].sudo().with_context(**ctx)
        domain = Product._search_qty_available('>', 0)
        domain = domain + [('is_medical_consumable', '=', True)] + extra_domain
        products = Product.search(domain)
        logging.info("Consumables: %s : Proudcts: %s", location.display_name, products)
        for prod in products:
            products_data.append({
                'id': prod.id,
                'name': prod.name,
                'display_name': prod.display_name,
                'qty_available': prod.with_context(**ctx).qty_available,
                'uom': prod.uom_id.name,
            })
        return products_data
