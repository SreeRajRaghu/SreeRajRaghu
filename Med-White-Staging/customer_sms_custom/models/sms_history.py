# -*- coding: utf-8 -*-
import requests

from odoo import models, api, fields, _
from odoo.exceptions import UserError

GATEWAY = '/knews/easy_api_query.aspx'


class SmsHistory(models.Model):
    _name = 'sms.history'
    _description = 'SMS History'
    _rec_name = 'config_id'
    _order = "sent_datetime desc"

    config_id = fields.Many2one('sms.config', string='SMS Gateway Configuration')
    partner_ids = fields.Many2many('res.partner', string='Partner')
    contact_number = fields.Char('Contact Number')
    message_text = fields.Text('Message')
    sent_datetime = fields.Datetime('Sent Date')
    status = fields.Text(string='Status')
    cost = fields.Float('Cost')
    remaining_balance = fields.Float('Remaining Balance')
    contact_lines = fields.One2many('sms.history.line', 'history_id', string='Contacts')
    is_error = fields.Boolean('Has Error')
    res_id = fields.Char("Record ID", index=True)
    notif_trigger_id = fields.Many2one('notif.trigger', string='Notif Trigger', index=True)
    language = fields.Selection([('en', 'English'), ('ar', 'Arabic')], default='en')

    def check_msg_status(self):
        for rec in self:
            for con in rec.contact_lines:
                if con.message_id:
                    url = rec.config_id.api_ip + GATEWAY + '?un=%s&pw=%s&msg_id=%s'
                    try:
                        url = url % (rec.config_id.username, rec.config_id.password, con.message_id)
                        response = requests.request("GET", url)
                        con.message_status = response.text
                    except Exception as e:
                        raise UserError(_(str(e)))

    def resend_sms(self):
        self.ensure_one()
        action = self.env.ref("easy_sms.action_send_sms").read()[0]
        ctx = dict(self.env.context)
        ctx.update({
            'default_partner_ids': self.partner_ids.ids,
            'default_config_id': self.config_id.id,
            'default_contact_list': self.contact_number,
            'default_message': self.message_text,
            'default_keep_sms_history': True,
        })
        action.update({"context": ctx})
        return action


class SmsHistoryLine(models.Model):
    _name = 'sms.history.line'
    _description = 'SMS History Line'

    message_id = fields.Char('Message ID')
    mobile = fields.Char('Mobile')
    is_approved = fields.Boolean('Approved')
    cost = fields.Float('Cost')
    history_id = fields.Many2one('sms.history', string='History')
    message_status = fields.Html('Message Status')
