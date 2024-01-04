# -*- coding: utf-8 -*-

from odoo import fields, models


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
    resource_id = fields.Many2one('medical.resource', string="Resource")

    def confirm_filter(self):
        dashboard_dashboard = self.env.context.get('dashboard_dashboard')
        dashboard = self.env['dashboard.settings'].browse([dashboard_dashboard])
        dashboard.write({
            'date_from': str(self.date_from) + ' 00:00:00',
            'date_to': str(self.date_to) + ' 23:59:59',
            'account_analytic_ids': [(6, 0, self.account_analytic_ids.ids)],
            'day': self.day,
            'month': self.month,
            'user_id': self.user_id.id,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
