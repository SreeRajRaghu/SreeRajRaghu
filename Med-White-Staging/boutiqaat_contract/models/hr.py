# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Contract(models.Model):
    _inherit = "hr.contract"

    housing_allowance = fields.Monetary("Housing / Accommodation Allowance", tracking=True)
    transport_allowance = fields.Monetary("Transport Allowance", tracking=True)
    mobile_allowance = fields.Monetary("Mobile Allowance", tracking=True)
    meal_allowance = fields.Monetary("Meal Allowance", tracking=True)
    motor_vehicle_allowance = fields.Monetary("Motor Vehicle Allowance", tracking=True)
    driver_fuel_allowance = fields.Monetary("Driver & Fuel Allowance", tracking=True)
    books_allowance = fields.Monetary("Books Allowance", tracking=True)
    special_other_allowance = fields.Monetary("Special / Other Allowance", tracking=True)
    commission = fields.Monetary("Commission", tracking=True)
    staff_discount = fields.Float("Staff Discount (%)", default=0.4, tracking=True)
    staff_max_discount = fields.Monetary("Staff Max Discount", default=60, tracking=True)
    pf_allowance = fields.Monetary("PF Allowances", tracking=True)
    night_shift_allowance = fields.Monetary("Night Shift Allowance", tracking=True)

    rot_rate = fields.Float(related="resource_calendar_id.rot_rate")
    wot_rate = fields.Float(related="resource_calendar_id.wot_rate")
    pot_rate = fields.Float(related="resource_calendar_id.pot_rate")
    tot_monthly_hours = fields.Float("Total Monthly Hours", compute="_compute_tot_monthly_hours", store=True, tracking=True)
    total_salary = fields.Float('Total Salary', compute="_compute_tot_salary", store=True, tracking=True)

    # Updated Salary
    next_contract_id = fields.Many2one('hr.contract', 'Next Contract', tracking=True)
    prev_contract_id = fields.Many2one('hr.contract', 'Prev. Contract', tracking=True)
    state = fields.Selection(selection_add=[('upd', 'Updated')])

    def action_update_contract(self):
        self.ensure_one()
        action = self.env.ref("boutiqaat_contract.action_upd_contract_wizard").read()[0]
        ctx = self.env.context.copy()
        ctx.update({
            'default_contract_id': self.id,
            'default_wage': self.wage,
            'default_name': self.name,
        })
        action.update({'context': ctx})
        return action

    @api.depends("hours_per_day", "month_days")
    def _compute_tot_monthly_hours(self):
        for rec in self:
            if rec.resource_calendar_id:
                rec.tot_monthly_hours = (rec.hours_per_day or 8) * (rec.month_days or 26)

    def get_all_allowance(self, with_alw=True, with_wage=True):
        tot = 0
        if with_alw:
            tot += self.housing_allowance + \
                        self.transport_allowance + \
                        self.mobile_allowance +\
                        self.meal_allowance +\
                        self.motor_vehicle_allowance +\
                        self.driver_fuel_allowance +\
                        self.books_allowance +\
                        self.special_other_allowance +\
                        self.commission +\
                        self.pf_allowance +\
                        self.night_shift_allowance
        if with_wage:
            tot += self.wage
        return tot

    @api.depends('housing_allowance', 'transport_allowance', 'mobile_allowance', 'meal_allowance', 'motor_vehicle_allowance',
                 'driver_fuel_allowance', 'books_allowance', 'special_other_allowance', 'commission', 'pf_allowance',
                 'night_shift_allowance', 'wage')
    def _compute_tot_salary(self):
        for rec in self:
            total = rec.housing_allowance + \
                        rec.transport_allowance + \
                        rec.mobile_allowance + \
                        rec.meal_allowance + \
                        rec.motor_vehicle_allowance + \
                        rec.driver_fuel_allowance + \
                        rec.books_allowance + \
                        rec.special_other_allowance + \
                        rec.commission + \
                        rec.pf_allowance + \
                        rec.night_shift_allowance + \
                        rec.wage
            rec.total_salary = total
