# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MedWaitingList(models.Model):
    _name = 'medical.waiting.list'
    _description = 'Waiting List'


class WaitingList(models.Model):
    _name = 'app.waiting.list'
    _description = 'Waiting List'
    _rec_name = 'date'

    date = fields.Date()
    resource_id = fields.Many2one('medical.resource')
    service_ids = fields.Many2many('product.product', 'product_product_waiting_list', string="Services")
    note = fields.Char()
    after_call_note = fields.Char()
    partner_id = fields.Many2one('res.partner')
    patient_mobile = fields.Char(related="partner_id.mobile")
    medical_config_id = fields.Many2one('medical.config', string="Scheduler", readonly=True)
    medical_order_id = fields.Many2one('medical.order')
    medical_order_line_ids = fields.One2many('medical.order.line', 'medical_waiting_list_id')
    state = fields.Selection([
        ('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
        default='draft', required=True)

    employee_id = fields.Many2one('hr.employee', string="Employee")
    branch_id = fields.Many2one("medical.clinic", string="Branch")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    def mark_as_done(self):
        self.write({'state': 'done'})
        return True

    def mark_as_canceled(self):
        self.write({'state': 'cancel'})
        return True

    @api.model
    def create_update_waiting(self, vals):
        # medical_order_line_ids = vals.pop('medical_order_line_ids')
        services_ids = [(5, 0, 0)] + [(6, 0, vals.get('service_ids'))]
        vals['service_ids'] = services_ids
        waitinglist = self.env['app.waiting.list']
        if vals.get('id'):
            waitinglist = waitinglist.browse(vals['id'])
            waitinglist.write(vals)
        else:
            waitinglist = waitinglist.create(vals)
        # self.env['medical.order.line'].browse(medical_order_line_ids).write({'order_id': False, 'medical_waiting_list_id': waitinglist.id})
        # medical_order = waitinglist.medical_order_id
        # if not medical_order.lines:
        #     medical_order.write({'active': False})
        return self.fetch_waiting_lines()

    def restore_to_appointment(self):
        poid = self.medical_order_id
        if poid:
            if poid.state in ['invoiced', 'paid', 'done', 'cancel']:
                return {'status': False,
                        'message': 'Cannot be restored due to' + poid.state}
            if not poid.active:
                poid.write({'active': True})
            self.medical_order_line_ids.write({'order_id': poid.id})
            self.unlink()
            return {'status': True}
        return {'status': False}

    def fetch_waiting_lines(self, extra_domain=None):
        extra_domain = extra_domain or []
        domain = [('date', '>=', fields.Date.today())]
        return self.search_read(domain + extra_domain)
