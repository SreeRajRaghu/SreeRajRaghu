# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models


class DashboardSettings(models.Model):
    _name = 'dashboard.settings'
    _description = 'Dashboard'

    def get_default_chart_model(self):
        return self.search([], limit=1, order='id desc').chart_model_id.id

    def get_default_chart_measure_field(self):
        return self.search([], limit=1, order='id desc').chart_measure_field_id.id

    def get_default_chart_date_field(self):
        return self.search([], limit=1, order='id desc').chart_date_field_id.id

    def get_default_lines(self):
        return self.search([], limit=1, order='id desc').line_ids.ids

    def get_default_chart(self):
        return self.search([], limit=1, order='id desc').chart_ids.ids

    name = fields.Char('Name', default="Setting")
    provider_latitude = fields.Char('latitude')
    provider_longitude = fields.Char('ongitude')
    map = fields.Char('ongitude')
    line_ids = fields.One2many('dashboard.settings.line', 'dashboard_id', 'Fields', default=get_default_lines)
    chart_ids = fields.One2many('dashboard.settings.chart', 'dashboard_id', 'Charts', default=get_default_chart)
    date_from = fields.Datetime('From', default=time.strftime('%Y-%m-%d 23:59:59'))
    date_to = fields.Datetime('To', default=time.strftime('%Y-%m-%d 00:00:00'))

    account_analytic_ids = fields.Many2many(
        'account.analytic.account',
        'analytic_account_dashboard_settings_rel',
        'dashboard_id',
        'account_analytic_id',
        string='Analytic Accounts')
    day = fields.Selection([('1', 'Monday'), ('2', 'Tuesday'), ('3', 'Wednesday'),
                            ('4', 'Thursday'), ('5', 'Friday'), ('6', 'Saturday'), ('7', 'Sunday')])
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'),
                              ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')])
    user_id = fields.Many2one('res.users', 'User')

    @api.model
    def button_dummy(self):
        dashboards = self.env['dashboard.settings'].search([])
        dashboards.write({
            'date_from': time.strftime('%Y-%m-%d') + ' 00:00:00',
            'date_to': time.strftime('%Y-%m-%d') + ' 23:59:59',
            'day': False,
            'month': False,
            'user_id': False,
            'account_analytic_ids': [(5, 0, 0)],
        })
        return True


class DashboardSettingsLine(models.Model):
    _name = 'dashboard.settings.line'
    _description = 'Dashboard'
    _order = "sequence"

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', 'Model')
    sequence = fields.Integer('Sequence', default=1)
    model = fields.Char(related="model_id.model")
    field_id = fields.Many2one(
        'ir.model.fields', 'Field',
        domain="[('model_id', '=', model_id)]")
    color = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green'),
        ('lightgreen', 'Light Green'),
        ('primary', 'Primary'),
        ('yellow', 'Yellow'),
        ('lightyellow', 'Light Yellow'),
        ('sandybrown', 'Sandy Brown'),
        ('don_juan', 'Don Juan'),  # 644D52
        ('coral', 'Coral'),  # F77A52
        ('sunshade', 'Sunshade'),  # FF974F
        ('outrageous', 'Outrageous Orange'),  # F54F29
        ('matisse', 'Matisse'),  # 375D81
        ('regent', 'Regent'),  # 91BED4
        ('air_force', 'Air Force'),  # 5B92A8
        ('heather', 'Heather'),  # 9DBDC6
        ('night', 'Night'),  # 3333333
    ], string='Color')
    icon = fields.Char('Icon')
    filter = fields.Char('Filter')
    type = fields.Selection([('money', 'Money'), ('qty', 'Quantity')], string='Type')
    dashboard_id = fields.Many2one('dashboard.settings', 'Setting')
    display = fields.Boolean('Show/hide', default=True)
    date_from = fields.Datetime(related='dashboard_id.date_from', store=True)
    date_to = fields.Datetime(related='dashboard_id.date_to', store=True)
    day = fields.Selection(related='dashboard_id.day', store=True)
    month = fields.Selection(related='dashboard_id.month', store=True)
    user_id = fields.Many2one('res.users', related='dashboard_id.user_id', store=True)
    custom_sql = fields.Text()
    custom_sql_ids = fields.Text()
    custom_sql_alias = fields.Char()
    action_id = fields.Many2one(
        'ir.actions.act_window',
        domain="[('res_model', '=', model)]",
        string="Action")
    char_groups = fields.Char(string='Groups', help="Comma-separated list of groups. eg. base.group_user")
    visibility = fields.Selection([('common', 'Common'), ('hr', "HR"), ('hr_state', 'HR Statistics')], string="common", default="common")
    is_aging = fields.Boolean()
    aging_action = fields.Many2one('ir.actions.client')
    show_only_today = fields.Boolean('Show Only Today')
    show_future = fields.Boolean('Show Future')
    show_all = fields.Boolean('Show All')
    apply_create_date_filter = fields.Boolean(default=True, help="uncheck if you have some other fields in mind :D")
    date_field_name = fields.Char(help="give date or datetime field name this will not apply create date by default")
    no_append = fields.Boolean(string='No append', help="This will execute only raw sql without any filters and conditions")
    has_code = fields.Boolean(string='Python Code', help="This will execute only python code, provide method name in custom_sql and return field and res_ids")
    company_id = fields.Many2one('res.company', string='Company')

    def copy_line(self):
        self.ensure_one()
        self.copy()


class DashboardSettingschart(models.Model):
    _name = 'dashboard.settings.chart'
    _description = "Dashboard Settings Chart"

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', default=1)
    display_type = fields.Selection([('area', 'Area'), ('bar', 'Bar')], string='Display Type')
    chart_model_id = fields.Many2one('ir.model', 'Chart Model')
    chart_measure_field_id = fields.Many2one('ir.model.fields', 'Chart measure Field')
    chart_date_field_id = fields.Many2one('ir.model.fields', 'Chart date Field')
    filter = fields.Char('Filter')
    type = fields.Selection([('money', 'Money'), ('qty', 'Quantity')], string='Type')
    dashboard_id = fields.Many2one('dashboard.settings', 'Setting')
    display = fields.Boolean('Show/hide', default=True)
    company_id = fields.Many2one('res.company', string='Company')

    @api.onchange('display_type', 'chart_model_id')
    def _onchange_price(self):
        domain = []
        if self.chart_model_id:
            domain.append(('model_id', '=', self.chart_model_id.id))
        if self.display_type:
            if self.display_type == 'area':
                domain += [(('ttype', 'in', ['date', 'datetime']))]
            else:
                domain += [(('ttype', 'in', ['date', 'datetime', 'many2one']))]
        return {
            'domain': {
                'chart_date_field_id': domain,
            }
        }
