# -*- coding: utf-8 -*-

from odoo import fields, models
from pytz import timezone, UTC
from odoo.tools import format_time
from datetime import datetime


def to_naive_user_tz(datetime, tz_name):
    tz = tz_name and timezone(tz_name) or UTC
    return UTC.localize(
        datetime.replace(tzinfo=None),
        is_dst=False).astimezone(tz).replace(tzinfo=None)


def to_naive_utc(datetime, tz_name='Asia/Kuwait'):
    tz = tz_name and timezone(tz_name) or UTC
    return tz.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(
        UTC).replace(tzinfo=None)


class FilterDates(models.TransientModel):
    _name = "filter.dates"
    _description = "Filter Dates"

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    account_analytic_ids = fields.Many2many(
                                'account.analytic.account',
                                'account_analytic_account_filter_rel',
                                'filter_date_id',
                                'account_analytic_id',
                                string='Analytic Accounts')
    day = fields.Selection([('1', 'Monday'), ('2', 'Tuesday'), ('3', 'Wednesday'),
                            ('4', 'Thursday'), ('5', 'Friday'), ('6', 'Saturday'), ('7', 'Sunday')])
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'),
                              ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')])
    user_id = fields.Many2one('res.users', 'User')

    def confirm_filter(self):
        # dashboard_dashboard = self.env.context.get('dashboard_dashboard')
        dashboard = self.env['dashboard.settings'].search([])
        dashboard.write({
            'date_from': datetime.combine(self.date_from, datetime.min.time()),
            'date_to': datetime.combine(self.date_to, datetime.max.time()),
            'account_analytic_ids': [(6, 0, self.account_analytic_ids.ids)],
            'day': self.day,
            'month': self.month,
            'user_id': self.user_id.id,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
