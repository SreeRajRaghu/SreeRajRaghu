# -*- coding: utf-8 -*-

import time

from odoo import fields, models, _
from odoo.exceptions import UserError


RESOURCE_FIELDS_IN_MODEL = {
    'pos.order': 'resource_id',
    'account.invoice': 'resource_id',
    'sm.waiting.list': 'resource_id'
}


class Dashboard(models.Model):
    _name = 'dashboard.dashboard'
    _description = 'Dashboard'

    def has_active(self, model):
        for field in model.field_id:
            if field.name == 'active':
                return True
        return False

    def _compute_field_list(self):
        dashboard = self.env['dashboard.settings'].search([], limit=1, order='id desc')
        last_slices_list = []
        ActWindow = self.env['ir.actions.act_window']
        visibility = self._context.get('dashboard_visibility') or 'common'
        lists = dashboard.line_ids.filtered(lambda r: r.visibility == visibility)

        date_from = dashboard.date_from
        date_to = dashboard.date_to
        account_analytic_ids = dashboard.account_analytic_ids.ids
        month = dashboard.month
        day = dashboard.day
        user_id = dashboard.user_id.id and str(dashboard.user_id.id)
        resource_ids = []
        today_date_from = time.strftime('%Y-%m-%d') + ' 00:00:00'
        today_date_to = time.strftime('%Y-%m-%d') + ' 23:59:59'

        for list in lists:
            alias = ""
            if list.display:
                filter_by_resources = False
                if list.model_id.model in RESOURCE_FIELDS_IN_MODEL and resource_ids:
                    filter_by_resources = True
                    resource_field = RESOURCE_FIELDS_IN_MODEL[list.model_id.model]

                action = list.action_id
                if not action:
                    action = ActWindow.search([('res_model', '=', list.model_id.model)], limit=1)
                requete_action = "Select id as id from " + list.model_id.model.replace('.', '_')
                if list.type == 'money':
                    requete = "SELECT sum(" + list.field_id.name + ") as field FROM " + list.model_id.model.replace('.',
                                                                                                                    '_')
                elif list.type == 'qty':
                    requete = "SELECT count(" + list.field_id.name + ") as field FROM " + list.model_id.model.replace(
                        '.', '_')
                date_from = today_date_from if list.show_only_today or not date_from else dashboard.date_from
                date_to = today_date_to if list.show_only_today or not date_to else dashboard.date_to
                company_id = self.env.company.id
                if list.show_future:
                    date_to = False

                if list.show_all:
                    date_from = False
                    date_to = False
                alias = list.custom_sql_alias or list.model_id.model.replace('.', '_')
                if list.custom_sql:
                    # requete_action = list.custom_sql
                    requete = list.custom_sql
                    if list.custom_sql_ids:
                        requete_action = list.custom_sql_ids

                    alias = list.custom_sql_alias or list.model_id.model.replace('.', '_')
                    if list.apply_create_date_filter or not list.date_field_name:
                        field_name = ".create_date"
                    else:
                        field_name = "."+list.date_field_name
                    if date_from:
                        requete += " AND " + alias + field_name + " >='" + str(date_from) + "'"
                        requete_action += " AND " + alias + field_name+" >='" + str(date_from) + "'"
                    if date_to:
                        requete += " AND " + alias + field_name+" <='" + str(date_to) + "'"
                        requete_action += " AND " + alias + field_name+" <='" + str(date_to) + "'"
                    if month:
                        requete += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                        requete_action += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                    if day:
                        requete += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                        requete_action += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                    if user_id:
                        requete += " AND " + alias + ".create_uid =" + user_id
                        requete_action += " AND " + alias + ".create_uid =" + user_id
                    if filter_by_resources:
                        if len(resource_ids) == 1:
                            requete += " AND " + alias + "." + resource_field + "=" + str(resource_ids[0])
                            requete_action += " AND " + alias + "." + resource_field + "=" + str(resource_ids[0])
                        else:
                            requete += " AND " + alias + "." + resource_field + " in " + str(tuple(resource_ids))
                            requete_action += " AND " + alias + "." + resource_field + " in " + str(
                                tuple(resource_ids))

                elif self.has_active(list.model_id) and list.filter:
                    requete += " Where active=true And " + list.filter
                    requete_action += " Where active=true And " + list.filter
                    if list.apply_create_date_filter or not list.date_field_name:
                        field_name = ".create_date"
                    else:
                        field_name = "." + list.date_field_name

                    if date_from:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" >='" + str(
                            date_from) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" >='" + str(
                            date_from) + "'"
                    if date_to:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" <='" + str(
                            date_to) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" <='" + str(
                            date_to) + "'"
                    if month:
                        requete += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                        requete_action += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                    if day:
                        requete += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                        requete_action += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                    if user_id:
                        requete += " AND " + alias + ".create_uid =" + user_id
                        requete_action += " AND " + alias + ".create_uid =" + user_id

                    if account_analytic_ids and list.model_id.model == 'pos.order':
                        if len(account_analytic_ids) > 1:
                            requete += " And " + list.model_id.model.replace('.',
                                                                             '_') + ".analytic_account_id in %s" % (
                                           tuple(account_analytic_ids),)
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id in %s" % (
                                                  tuple(account_analytic_ids),)
                        else:
                            requete += " And " + list.model_id.model.replace('.', '_') + ".analytic_account_id = %s" % \
                                       account_analytic_ids[0]
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id = %s" % \
                                              account_analytic_ids[0]
                    if filter_by_resources:
                        if len(resource_ids) == 1:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                        else:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))

                elif self.has_active(list.model_id):
                    requete += " Where active=true "
                    requete_action += " Where active=true "
                    if list.apply_create_date_filter or not list.date_field_name:
                        field_name = ".create_date"
                    else:
                        field_name = "." + list.date_field_name

                    if date_from:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" >='" + str(
                            date_from) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" >='" + str(
                            date_from) + "'"
                    if date_to:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" <='" + str(
                            date_to) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" <='" + str(
                            date_to) + "'"
                    if month:
                        requete += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                        requete_action += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                    if day:
                        requete += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                        requete_action += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                    if user_id:
                        requete += " AND " + alias + ".create_uid =" + user_id
                        requete_action += " AND " + alias + ".create_uid =" + user_id

                    if account_analytic_ids and list.model_id.model == 'pos.order':
                        if len(account_analytic_ids) > 1:
                            requete += " And " + list.model_id.model.replace('.',
                                                                             '_') + ".analytic_account_id in %s" % (
                                           tuple(account_analytic_ids),)
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id in %s" % (
                                                  tuple(account_analytic_ids),)
                        else:
                            requete += " And " + list.model_id.model.replace('.', '_') + ".analytic_account_id = %s" % \
                                       account_analytic_ids[0]
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id = %s" % \
                                              account_analytic_ids[0]
                    if filter_by_resources:
                        if len(resource_ids) == 1:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                        else:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))

                elif list.filter:
                    requete += " Where " + list.filter
                    requete_action += " Where " + list.filter
                    if list.apply_create_date_filter or not list.date_field_name:
                        field_name = ".create_date"
                    else:
                        field_name = "." + list.date_field_name

                    if date_from:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" >='" + str(
                            date_from) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" >='" + str(
                            date_from) + "'"
                    if date_to:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" <='" + str(
                            date_to) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" <='" + str(
                            date_to) + "'"
                    if month:
                        requete += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                        requete_action += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                    if day:
                        requete += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                        requete_action += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                    if user_id:
                        requete += " AND " + alias + ".create_uid =" + user_id
                        requete_action += " AND " + alias + ".create_uid =" + user_id
                    if account_analytic_ids and list.model_id.model == 'pos.order':
                        if len(account_analytic_ids) > 1:
                            requete += " And " + list.model_id.model.replace('.',
                                                                             '_') + ".analytic_account_id in %s" % (
                                           tuple(account_analytic_ids),)
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id in %s" % (
                                                  tuple(account_analytic_ids),)
                        else:
                            requete += " And " + list.model_id.model.replace('.', '_') + ".analytic_account_id = %s" % \
                                       account_analytic_ids[0]
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id = %s" % \
                                              account_analytic_ids[0]
                    if filter_by_resources:
                        if len(resource_ids) == 1:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                        else:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))
                else:
                    if list.apply_create_date_filter or not list.date_field_name:
                        field_name = ".create_date"
                    else:
                        field_name = "." + list.date_field_name

                    if date_from:
                        requete += " Where " + list.model_id.model.replace('.', '_') + field_name+" >='" + str(
                            date_from) + "'"
                        requete_action += " Where " + list.model_id.model.replace('.',
                                                                                  '_') + field_name+" >='" + str(
                            date_from) + "'"
                    if date_to:
                        requete += " And " + list.model_id.model.replace('.', '_') + field_name+" <='" + str(
                            date_to) + "'"
                        requete_action += " And " + list.model_id.model.replace('.',
                                                                                '_') + field_name+" <='" + str(
                            date_to) + "'"
                    if month:
                        requete += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                        requete_action += " AND EXTRACT(month FROM " + alias + field_name+") =" + str(month % 12)
                    if day:
                        requete += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                        requete_action += " AND EXTRACT(dow FROM " + alias + field_name+") =" + str(day % 7)
                    if user_id:
                        requete += " AND " + alias + ".create_uid =" + user_id
                        requete_action += " AND " + alias + ".create_uid =" + user_id
                    if account_analytic_ids and list.model_id.model == 'pos.order':
                        if len(account_analytic_ids) > 1:
                            requete += " And " + list.model_id.model.replace('.',
                                                                             '_') + ".analytic_account_id in %s" % (
                                           tuple(account_analytic_ids),)
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id in %s" % (
                                                  tuple(account_analytic_ids),)
                        else:
                            requete += " And " + list.model_id.model.replace('.', '_') + ".analytic_account_id = %s" % \
                                       account_analytic_ids[0]
                            requete_action += " And " + list.model_id.model.replace('.',
                                                                                    '_') + ".analytic_account_id = %s" % \
                                              account_analytic_ids[0]
                    if filter_by_resources:
                        if len(resource_ids) == 1:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + "=" + str(
                                resource_ids[0])
                        else:
                            requete += " AND " + list.model_id.model.replace('.',
                                                                             '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))
                            requete_action += " AND " + list.model_id.model.replace('.',
                                                                                    '_') + "." + resource_field + " in " + str(
                                tuple(resource_ids))

                if list.model_id.field_id.filtered(lambda l: l.name == 'company_id' and (not l.related or l.store)):
                    requete += " AND " + alias + "." + 'company_id' + "=" + str(company_id)
                    requete_action += " AND " + alias + "." + 'company_id' + "=" + str(company_id)

                res_ids = []
                if list.is_aging:
                    field = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines(['receivable'],
                                                                                                         date_to.strftime('%Y-%m-%d'),
                                                                                                         'posted', 30)
                    field = field[1][-1]
                    action = list.aging_action
                else:
                    if list.has_code:
                        field, res_ids = getattr(self.env[list.model_id.model], list.custom_sql)(list)
                    else:
                        if list.no_append:
                            if list.custom_sql:
                                requete = list.custom_sql.format(date_from=date_from, date_to=date_to, company_id=int(company_id))
                            if list.custom_sql_ids:
                                requete_action = list.custom_sql_ids.format(date_from=date_from, date_to=date_to, company_id=int(company_id))

                        print ('_ requete : ', requete)
                        self.env.cr.execute(requete.replace('"', "'"))
                        result = self.env.cr.dictfetchall()
                        field = result and result[0].get('field', 0) or 0
                        self.env.cr.execute(requete_action.replace('"', "'"))
                        result_ids = self.env.cr.dictfetchall()
                        for res in result_ids:
                            if res.get('id'):
                                res_ids.append(res['id'])
                last_slices_list.append(
                    [field, list.name or list.field_id.field_description, list.color, list.icon, action.id, res_ids,
                     int(list.is_aging)])
        return last_slices_list

    def _get_default_chart(self):
        chart_list = []
        dashboard = self.env['dashboard.settings'].search([], limit=1, order='id desc')
        chart_ids = self.env['dashboard.settings.chart'].search([('dashboard_id', '=', dashboard.id)], order='sequence')
        date_from = dashboard.date_from
        date_to = dashboard.date_to
        if not date_from:
            date_from = time.strftime('%Y-%m-%d') + ' 00:00:00'
        if not date_to:
            date_to = time.strftime('%Y-%m-%d') + ' 23:59:59'

        user = self.env.user
        for list in chart_ids:
            if list.char_groups and not user.sudo(user.id).has_group(str(list.char_groups)):
                continue
            if list.display:
                filter = ""
                if date_from:
                    filter = "create_date >='" + str(date_from) + "'"
                if date_to:
                    filter += " And create_date <='" + str(date_to) + "'"
                list.fiter = filter
                list.write({'filter': filter})
                if list.display_type == 'area':
                    chart_list.append([list.id, list.name, 1])
                else:
                    chart_list.append([list.id, list.name, 2])
        return chart_list

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, string="Currency")
    field_list = fields.Selection('_compute_field_list', string='Slices names')
    chart_list = fields.Selection('_get_default_chart', string='Charts')

    def action_setting(self):
        action = self.env.ref('dashboard.action_dashboard_config').read()[0]
        setting = self.env['dashboard.settings'].search([], limit=1, order='id desc').id
        action['views'] = [(self.env.ref('dashboard.dashboard_config_settings').id, 'form')]
        action['res_id'] = setting
        return action

    def view_details(self):
        record_ids = self.env.context.get('record_ids')
        if not record_ids:
            raise UserError(_("No Records To Show."))
        action_id = self.env.context.get('action_id')
        result = {}
        if action_id:
            if not self.env.context.get('is_aging'):
                Model = self.env['ir.actions.act_window']
            else:
                Model = self.env['ir.actions.client']
            action = Model.browse(action_id)
            if action:
                result = action.read()[0]

            if result and record_ids:
                result['domain'] = [('id', 'in', record_ids)]
        return result
