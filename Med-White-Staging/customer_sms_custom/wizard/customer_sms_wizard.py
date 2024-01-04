# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
from collections import defaultdict
import requests
import logging

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import json

_logger = logging.getLogger(__name__)
GATEWAY = '/messaging/SendSMS'


class SendSms(models.TransientModel):
    _name = "customer.sms.send"
    _description = 'Customer Send SMS'

    config_id = fields.Many2one('sms.config', string='SMS Gateway', required=True)
    partner_ids = fields.Many2many('res.partner', string='Customers')
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'),
                              ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')])
    sms_template_id = fields.Many2one('sms.sms.template', string='Template')
    message = fields.Text('Message')
    keep_sms_history = fields.Boolean("Keep History", default=True)
    res_id = fields.Char("Record ID")
    notif_trigger_id = fields.Many2one('notif.trigger', string='Notif Trigger')
    language = fields.Selection([('en', 'English'), ('ar', 'Arabic')], default='en')

    @api.onchange('sms_template_id')
    def _onchange_template_id(self):
        if self.sms_template_id:
            self.message = self.sms_template_id.body_text
        else:
            self.message = ''

    @api.onchange('month')
    def _onchange_partner(self):
        if self.month:
            partner_list = self.env['res.partner'].search([('birthday', '!=', False)]).filtered(lambda r: r.birthday.month == int(self.month)).ids
            if not partner_list:
                return {'domain': {'partner_ids': []}}

            domain = [('id', 'in', partner_list)]
            return {'domain': {'partner_ids': domain}}
        else:
            return {'domain': {'partner_ids': []}}

    def send_sms(self):
        self.ensure_one()
        if self.config_id:
            msg = self.env['sms.sms.template'].search([('code', '=', 'customer_bday')], limit=1).body_text
            # msg = self.message
            # msg = str.encode(self.message)
            # msg.strip()
            if (self.language or self.config_id.language) == 'ar':
                msg = self.message.encode('utf-16-be')
            for partner in self.partner_ids.filtered(lambda r: r.phone or r.mobile):
                number = str(partner.phone)
                customer_name = partner.name
                if '965' not in number:
                    if len(number) == 8 and not number.startswith('965'):
                        number = "965%s" % number
                # payload = {
                #     "username": self.config_id.username,
                #     "password": self.config_id.password,
                #     "messagebody": msg,
                #     "sender": self.config_id.sender_name,
                #     "number": int(number)
                # }

                message = msg % customer_name
                payload = {
                    "username": self.config_id.username,
                    "password": self.config_id.password,
                    "type": 0,
                    "dlr": 1,
                    "destination": int(number),
                    "source": self.config_id.sender_name,
                    "message": message,

                }

                headers = {
                    'Content-Type': 'application/json'
                }

                # url = self.config_id.api_ip + GATEWAY
                url = self.config_id.api_ip + "username="+str(self.config_id.username)+"&password="+str(self.config_id.password)+"&type=0&dlr=1&destination="+str(int(number))+"&source="+str(self.config_id.sender_name)+"&message="+str(message)
                url_wop = self.config_id.api_ip +"&type=0&dlr=1&destination="+str(int(number))+"&source="+str(self.config_id.sender_name)+"&message="+str(message)
                try:
                    # new_payload = json.dumps(payload, indent=4)
                    # _logger.info("Sending SMS: %s \n%s", url, new_payload)
                    _logger.info("Sending SMS:\n%s", url_wop)
                    # response = requests.request("POST", url, headers=headers, data=new_payload)
                    response = requests.post(url)
                    _logger.info("SMS Response: %s, %s", response, response.text)
                except Exception as e:
                    raise UserError(_(str(e)))
                if self.keep_sms_history:
                    self.create_sms_history(response, self.config_id, payload)
        return False

    def create_sms_history(self, resp, config, params):
        has_error = resp.status_code != 200
        body = params.get('message')
        if body and self.language == 'ar':
            body = body.decode('utf-8')
        vals = {
            'config_id': config.id,
            'contact_number': params.get('destination'),
            'message_text': body,
            'sent_datetime': fields.Datetime.now(),
            'is_error': has_error,
            'status': has_error and "Error %s" % (resp.text) or 'Success',
            'res_id': self.res_id,
            'notif_trigger_id': self.notif_trigger_id.id,
            'language': self.language,
        }
        history = self.env['sms.history'].sudo().create(vals)
        model = self.notif_trigger_id.model_id.model
        if history and model and self.res_id:
            try:
                record = self.env[model].sudo().browse(int(self.res_id))
                if record:
                    body = "SMS Sent to : %s <br />" + body % (history.contact_number)
                    record.message_post(body=body)
            except Exception as e:
                _logger.info("__ Exception : %s", str(e))
