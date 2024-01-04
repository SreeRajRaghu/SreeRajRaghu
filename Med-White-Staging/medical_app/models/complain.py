# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PatientComplain(models.Model):
    _name = "patient.complain"
    _description = "Patient Complain"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    complain_date = fields.Datetime("Complain Date", default=fields.Datetime.now, required=True)
    appointment_id = fields.Many2one("medical.order", string="Appointment")
    partner_id = fields.Many2one("res.partner", related="appointment_id.partner_id", string="Patient")
    clinic_id = fields.Many2one("medical.clinic", related="appointment_id.clinic_id", string="Branch")
    visit_date = fields.Datetime("Visit Date", related="appointment_id.date_arrived")
    complain_type_id = fields.Many2one("complain.type", string="Complain Type", tracking=20)
    complain = fields.Text()
    resolution = fields.Text()
    is_customer_satisfied = fields.Boolean("Customer Satisfied")
    create_eid = fields.Many2one("hr.employee", string="Created By")
    resolved_eid = fields.Many2one("hr.employee", string="Resolved By")
    resolved_on = fields.Datetime("Resolved On")
    state = fields.Selection([
        ('draft', 'Draft'), ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'), ('cancel', 'Canceled'),
        ('not_resolved', 'Not Resolved')],
        default='draft', tracking=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            seq = self.env['ir.sequence'].next_by_code('complain.sequence')
            vals['name'] = seq
        return super(PatientComplain, self).create(vals)

    def write(self, vals):
        if vals.get('state') == 'resolved':
            vals['resolved_on'] = fields.Datetime.now()
        return super(PatientComplain, self).write(vals)


class ComplainType(models.Model):
    _name = "complain.type"
    _description = "Complain Type"

    name = fields.Char(required=True)
