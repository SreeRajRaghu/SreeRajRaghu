# -*- coding: utf-8 -*-

from odoo import fields, models


class MedicalReminder(models.Model):
    _name = 'medical.reminder'
    _description = "Medical Reminder"

    name = fields.Char('Subject', required=True)


class AppReminder(models.Model):
    _name = 'app.reminder'
    _description = "Medical Reminder"
    _order = "todo_date DESC"

    name = fields.Char('Subject', required=True)
    description = fields.Text("Description")
    todo_date = fields.Date("Date", required=True, default=fields.Date.today)
    date_action = fields.Datetime("Action Date")
    user_id = fields.Many2one("res.users", string='Action Performed By', default=lambda self: self.env.uid)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')], default='draft')
    medical_order_id = fields.Many2one('medical.order', 'Appointment')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    def action_done(self):
        self.write({'state': 'done', 'date_action': fields.Datetime.now()})
        return True

    def update_state(self, state):
        return self.write({
            'state': state,
            'date_action': fields.Datetime.now()
        })
