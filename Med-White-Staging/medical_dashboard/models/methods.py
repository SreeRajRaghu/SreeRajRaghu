# -*- coding: utf-8 -*-

import calendar

from odoo import fields, models


def get_month(date):
    date_from = type(date)(date.year, date.month, 1)
    date_to = type(date)(date.year, date.month, calendar.monthrange(date.year, date.month)[1])
    return date_from, date_to


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def d_employee_absent_rate(self, dline):
        date_from, date_to = get_month(fields.Date.from_string(dline.date_from))
        self.env.cr.execute("""
            SELECT (SELECT sum(number_of_days) FROM hr_holidays WHERE date_from >= '2018-11-01' AND date_to <= '2018-11-30') / (SELECT (((SELECT count(date_start) FROM hr_contract WHERE date_start <= '2019-04-01') + (SELECT count(id) FROM hr_contract WHERE date_start <= '2019-04-01' AND date_end > '2019-04-30' OR date_end is null)) / 2.0) * 26)
        """.format(date_from, date_to))

        nod_mon = sum(self.env['hr.holidays'].search([('date_from', '>=', date_from), ('date_to', '<=', date_to)]).mapped('number_of_days'))
        start_employees = self.env['hr.contract'].search([('date_end', '>=', date_from), ('date_start', '<=', date_from), ('state', '=', 'open')]).mapped('employee_id')
        stop_employees = self.env['hr.contract'].search([('date_end', '>=', date_to), ('state', '=', 'open')]).mapped('employee_id')
        avg_emp = (len(start_employees) + len(stop_employees)) / 2
        total_employees = start_employees | stop_employees
        all_days = sum([e.resource_id.calendar_id.month_days for e in total_employees])
        avg_wdays = all_days / len(total_employees)
        field = nod_mon / (avg_emp * avg_wdays)
        return field, total_employees.ids
