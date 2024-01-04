# coding: utf-8

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

TERMINATE_REASON = [
    ("terminate", "Terminate"),
    ("resign", "Resign"),
    ('dismissed', 'Dismissed'),
    ("other", "Other")
]

SEL_RELIGION = [
    ('muslim', 'Muslim'),
    ('non_muslim', 'Non Muslim')
]
SEL_MAR_STATUS = [
    ('single', 'Single'),
    ('married', 'Married'),
    ('not_specific', 'Not Specific'),
    ('divorced', 'Divorced')
]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    civil_id = fields.Char('Civil ID')
    civil_start_date = fields.Date('Civil Start Date')
    civil_end_date = fields.Date('Civil End Date')
    # social_sec_date = fields.Datetime("Start Date")
    # social_sec_code = fields.Char("Social Security Code")
    work_permit_expiry = fields.Date("Work Permit Expiry")

    passport_start_date = fields.Date('Passport Start Date')
    passport_end_date = fields.Date('Passport End Date')
    passport_country_id = fields.Many2one('res.country', 'Passport Country')
    passport_type = fields.Char('Passport Type', default='Normal')
    sponsorship_id = fields.Many2one('res.partner', string="Sponsorship")
    iban_no = fields.Char("IBAN / Bank Account")

    # religion = fields.Char('Religion')
    religion = fields.Selection(SEL_RELIGION, string='Religion In', default='muslim')
    date_joining = fields.Date('Joining Date')
    date_job_end = fields.Date("Job End Date")
    job_end_reason = fields.Selection(TERMINATE_REASON, string="Job End Reason")
    job_end_desc = fields.Text("Job End Description")

    file_civil_id = fields.Binary("Civil Code Copy")
    file_driving_lic = fields.Binary("Driving License Copy")
    file_passport = fields.Binary("Passport Copy")

    article_type_id = fields.Many2one('article.type', string="Attachment Type")
    file_attachment = fields.Binary("Other Doc")

    residency_expiry_date = fields.Date('Residency Expiry Date')
    residency_number = fields.Char('Residency Number')
    work_permit_marital_status = fields.Selection(SEL_MAR_STATUS, string='Work Permit Marital Status')
    work_start_issue_date = fields.Date('Work Start Issued Date/ Joining Date')

    @api.constrains('passport_start_date', 'passport_end_date')
    def _check_passport_start_end_date(self):
        for employee in self:
            if employee.passport_start_date and employee.passport_end_date and employee.passport_end_date < employee.passport_start_date:
                raise ValidationError(
                    _('Ending date cannot be greater than starting date.') + "\n" +
                    _("Passport Of '%s' starts '%s' and ends '%s'") % (employee.name, employee.passport_start_date, employee.passport_end_date))

    @api.constrains('civil_start_date', 'civil_end_date')
    def _check_civil_start_end_date(self):
        for employee in self:
            if employee.civil_start_date and employee.civil_end_date and employee.civil_end_date < employee.civil_start_date:
                raise ValidationError(
                    _('Ending date cannot greater than starting date.') + "\n" +
                    _("Civil Of '%s' starts '%s' and ends '%s'") % (employee.name, employee.civil_start_date, employee.civil_end_date))

    def _get_date_start_work(self):
        if self.date_joining:
            return datetime.combine(self.date_joining, time.min)
        return self.create_date


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    civil_id = fields.Char(readonly=True)
    civil_start_date = fields.Date(readonly=True)
    civil_end_date = fields.Date(readonly=True)
    # social_sec_date = fields.Datetreadonly=True)
    # social_sec_code = fields.Char("Social Security Code")
    work_permit_expiry = fields.Date(readonly=True)
    passport_start_date = fields.Date(readonly=True)
    passport_end_date = fields.Date(readonly=True)
    iban_no = fields.Char("IBAN / Bank Account")

    passport_type = fields.Char(readonly=True)
    religion = fields.Selection(SEL_RELIGION, readonly=True)
    date_joining = fields.Date(readonly=True)
    date_job_end = fields.Date(readonly=True)
    job_end_reason = fields.Selection(TERMINATE_REASON, readonly=True)
    job_end_desc = fields.Text(readonly=True)
    # file_civil_id = fields.Binary(readonly=True)
    # file_driving_lic = fields.Binary(readonly=True)
    # file_passport = fields.Binary(readonly=True)
    article_type_id = fields.Many2one('article.type', readonly=True)
    # file_attachment = fields.Binary(readonly=True)
    passport_country_id = fields.Many2one('res.country', 'Passport Country', readonly=True)
    sponsorship_id = fields.Many2one('res.partner', string="Sponsorship", readonly=True)
    residency_expiry_date = fields.Date('Residency Expiry Date')
    residency_number = fields.Char('Residency Number')
    work_permit_marital_status = fields.Selection(SEL_MAR_STATUS, string='Work Permit Marital Status')
    work_start_issue_date = fields.Date('Work Start Issued Date/ Joining Date')


class Contract(models.Model):
    _inherit = 'hr.contract'

    month_days = fields.Float(related="resource_calendar_id.month_days")
    hours_per_day = fields.Float(related="resource_calendar_id.hours_per_day")
    prob_period_days = fields.Integer(related="resource_calendar_id.prob_period_days")
    prob_exclude_off = fields.Boolean(related="resource_calendar_id.prob_exclude_off")
    contract_type = fields.Char('Contract Type')
    permit_wage = fields.Monetary('Work Permit Salary')

    @api.onchange('resource_calendar_id', 'month_days', 'date_start')
    def onchange_probation(self):
        self.prob_date_end = False
        if self.date_start and self.prob_period_days and self.employee_id:
            dt = fields.Datetime.from_string("%s 00:00:00" % self.date_start).astimezone()
            if self.prob_exclude_off:
                calendar = self.resource_calendar_id
                date_end = calendar.plan_days(self.prob_period_days, dt, True)
            else:
                date_end = dt + relativedelta(days=self.prob_period_days)
            self.trial_date_end = date_end

    def write(self, vals):
        """
        If Contract Archive
        -> Set Contract End Date
        -> Set Contract as Expired

        If This Contract is linked in Employee
        -> Set another contract based on Date Else None
        """
        today = fields.Date.today()
        if 'active' in vals and vals['active'] == False:
            if not vals.get('date_end'):
                vals['date_end'] = today
            if not vals.get('state'):
                vals['state'] = 'close'
        res = super(Contract, self).write(vals)

        if ('active' in vals and vals['active'] == False) or (vals.get('date_end')):
            Employee = self.env['hr.employee']
            for contract in self:
                emps = Employee.search([('contract_id', '=', contract.id)])
                if emps:
                    emps.write({'contract_id': False})
        return res

    def get_all_allowance(self, with_alw=True, with_wage=True):
        tot = 0
        if with_wage:
            tot += self.wage
        return tot

    def get_per_day_salary(self, with_alw=True, with_wage=True):
        salary = self.get_all_allowance(with_alw, with_wage)
        print(salary,"*************************salary********")
        return salary / (self.month_days or 26)

    def get_per_hour_salary(self, with_alw=True, with_wage=True):
        salary = self.get_per_day_salary(with_alw, with_wage)
        return salary / (self.hours_per_day or 8)
