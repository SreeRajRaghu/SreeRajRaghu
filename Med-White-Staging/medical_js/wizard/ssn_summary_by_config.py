# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MedicalSessionSummary(models.TransientModel):
    _name = 'medical.session.summary'
    _description = 'Appointment Resource Details Report'

    start_date = fields.Date(default=fields.Date.context_today, string='Start Date')
    end_date = fields.Date(default=fields.Date.context_today, string='End Date')
    config_ids = fields.Many2many('medical.config', required=True, string='Schedulers')
    session_ids = fields.Many2many('medical.session', required=True, string='Sessions', domain="[('config_id', 'in', config_ids)]")

    @api.onchange("config_ids")
    def onchange_config_ids(self):
        self.session_ids = False

    def generate_report(self):
        data = {
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'config_ids': self.config_ids.ids,
            'session_ids': self.session_ids.ids,
        }
        return self.env.ref('medical_js.medical_session_by_config_report_action').report_action([], data=data)


class ReportResourceDetails(models.AbstractModel):
    _name = 'report.medical_js.session_summary_by_config_report_template'
    _description = "Report Medical Session By Config"

    @api.model
    def get_res_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        print ('___ date_start : ', date_start, date_stop, config_ids)
        today = fields.Date.today()
        config_ids = config_ids or []
        date_start = (date_start or today) + " 00:00:00"
        date_stop = (date_stop or today) + " 23:59:59"

        domain = []

        if session_ids:
            domain += [('id', 'in', session_ids)]
        elif config_ids:
            domain += [('config_id', 'in', config_ids)]

        sessions = self.env['medical.session'].search(domain)
        # session_data = []

        return {
            'from_date': date_start,
            'configs': sessions.mapped("config_id"),
            'sessions': sessions
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        order_list = self.get_res_details(data['date_start'], data['date_stop'], data['config_ids'])
        return order_list
