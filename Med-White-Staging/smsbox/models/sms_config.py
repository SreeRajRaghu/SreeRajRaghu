# -*- coding: utf-8 -*-
import requests
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging


# DEFAULT_END_POINT = 'https://api.smsbox.com/api'
_logger = logging.getLogger(__name__)


class SMSConfig(models.Model):
    _name = 'sms.config'
    _description = 'Sms Configuration'

    name = fields.Char('Name', required=True, default='Saloon One')
    active = fields.Boolean(string='Active', default=True)
    api_ip = fields.Char('API', required=True)
    username = fields.Char("Username")
    password = fields.Char("Password")
    sender_name = fields.Char("Sender Name")
    language = fields.Selection([('en', 'English'), ('ar', 'Arabic')],
                                default='en')
    state = fields.Selection([('draft', 'Not Connected'), ('connected', 'Connected')],
                             default='draft')
    msg_history = fields.One2many('sms.history', 'config_id', string='History')
    msg_history_count = fields.Integer(compute='_compute_msg_history', string='All History')

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default=lambda self: self.env.company.company_code)
    # balance_count = fields.Float(string='Balance')
    # sender_key = fields.Char("Sender ID", default='478')
    # send_type = fields.Char("Send Type", default='1')
    # api_key =  fields.Char('API Key', required=True)

    def _compute_msg_history(self):
        for config in self:
            config.msg_history_count = len(config.msg_history.ids)

    # def fetch_balance(self):
    #     for config in self:
    #         url = self.api_ip + '/cpanel/balance?api_key=' + self.api_key
    #         r = requests.request("GET", url).json()
    #         try:
    #             config.balance_count = float(r['Balance'])
    #         except Exception as e:
    #             raise UserError(_(str(e)))

    def test_connection(self):
        self.ensure_one()
        url = self.api_ip + '/cpanel/sender_ids?api_key=' + self.api_key
        response = requests.request("GET", url)

        if 'error' in response.text:
            raise UserError(_('Invalid API Key'))
        self.write({'state': 'connected'})
        return response

    def get_history(self):
        history = self.env['sms.history'].search([('config_id', '=', self.id)])
        return {
            'name': "Histories",
            'view_mode': 'tree,form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'sms.history',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', history.ids)],
        }
