# -*- coding: utf-8 -*-
import operator
import itertools

from odoo import api, fields, models


class MedicalDetails(models.TransientModel):
    _name = 'medical.resource.details.wizard'
    _description = 'Appointment Resource Details Report'

    start_date = fields.Date(required=True, default=fields.Date.context_today, string='Start Date')
    end_date = fields.Date(required=True, default=fields.Date.context_today, string='End Date')
    resource_ids = fields.Many2many('medical.resource', required=True, string='Resource')

    def generate_report(self):
        data = {
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'resource_ids': self.resource_ids.ids,
        }
        return self.env.ref('medical_js.appointment_resource_details_report').report_action([], data=data)


class ReportResourceDetails(models.AbstractModel):
    _name = 'report.medical_js.medical_resource_report_template'
    _description = "Report Medical Resource Appointments"

    @api.model
    def get_res_details(self, date_start=False, date_stop=False, resource_ids=False):
        today = fields.Date.today()
        resource_ids = resource_ids or []
        date_start = (date_start or today) + " 00:00:00"
        date_stop = (date_stop or today) + " 23:59:59"

        res_domain = []
        app_domain = [
            ('start_time', '>=', date_start),
            ('end_time', '<=', date_stop)
        ]
        if resource_ids:
            res_domain = [('id', 'in', resource_ids)]
            app_domain += [('resource_id', 'in', resource_ids)]

        resources = self.env['medical.resource'].search(res_domain)
        orders = self.env['medical.order'].search(app_domain, order='start_time')
        config = orders and orders[0].config_id or self.env['medical.config']
        company = orders and orders[0].company_id or self.env.company
        res_list = []
        for res in resources:
            order_list = []
            appointments = orders.filtered(lambda o: o.resource_id.id in resource_ids)
            total = len(appointments)
            for order in appointments:
                partner = order.partner_id
                order_list.append({
                    'resource_name': order.resource_id.name,
                    'app_date': fields.Date.to_string(order.start_time),
                    'start_time': order.start_time,
                    'end_time': order.end_time,
                    # 'state': dict(DEF_STATES).get(order.state),
                    'client': partner.name,
                    'file': partner.file_no if order.config_id.depends_on == 'file_no' else partner.file_no2,
                    'mobile': partner.mobile or partner.phone or False,
                    'note': order.note,
                    'services': order.line_ids.mapped('product_id').read(['name']),
                    'order': order,
                    'is_first': order.is_first
                })

            group_order_list = []
            order_list.sort(key=operator.itemgetter('app_date'))
            for k, v in itertools.groupby(order_list, operator.itemgetter('app_date')):
                group_order_list.append(list(v))
            res_list.append({
                'resource_id': res.id,
                'resource_name': res.name,
                'total_appointments': total,
                'order_list': group_order_list
            })
        return {
            'from_date': date_start,
            'to_date': date_stop,
            'resource_list': res_list,
            'config': config,
            'company': company
        }

    # def get_report_values(self, docids, data=None):
    #     data = dict(data or {})
    #     order_list = self.get_res_details(data['date_start'], data['date_stop'], data['resource_ids'])
    #     return order_list

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        order_list = self.get_res_details(data['date_start'], data['date_stop'], data['resource_ids'])
        return order_list
