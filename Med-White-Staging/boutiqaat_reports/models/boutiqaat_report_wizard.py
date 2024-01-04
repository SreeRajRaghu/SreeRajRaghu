# -*- coding: utf-8 -*-

from odoo import api, fields, models

REPORT_NAME_SELECTION = [
    ('salary_certificate', 'Salary Certificate'),
    ('salary_continous_certificate', 'Salary Continuity Certificate'),
    ('experience_certificate', 'Experience Certificate'),
    ('end_of_service_3_months', 'End of Service 3 months'),
    ('termination_during_probation_period', 'Termination During Probation Period'),
    ('resignation_during_probation_period', 'Resignation During Probation Period'),
    ('resignation_with_notice_period', 'Resignation With Notice Period'),
    ('resignation_with_out_notice_period', 'Resignation With Out Notice Period'),
    ('dismissal_order', 'Dismissal Order'),
    ('dismissal_order_article_41A3', 'Dismissal Order Article 41a3'),
    ('dismissal_order_article_41B1', 'Dismissal Order Article 41b1'),
    ('dismissal_order_article_41B2', 'Dismissal Order Article 41b2'),
    ('warning_letter', 'Warning Letter'),
    ('subj_suspension', 'Subj Suspension'),
    ('salary_increment', 'Salary Increment'),
    ('payment_request', 'Payment Request'),
    # ('pay_slip', 'Pay Slip'),
]

REPORT_NAME_SELECTION_AR = [
    ('salary_certificate', 'شهادة راتب'),
    ('salary_continous_certificate', 'شهادة استمرارية عمل'),
    ('experience_certificate', 'شهادة خبرة '),
    ('end_of_service_3_months', 'انهاء خدمات'),
    ('termination_during_probation_period', 'انهاء خدمات خلال فترة التجربة'),
    ('resignation_during_probation_period', 'قبول استقالة'),
    ('resignation_with_notice_period', 'قبول استقالة مع فترة انذار'),
    ('resignation_with_out_notice_period', 'قبول استقالة بدون فترة انذار'),
    ('dismissal_order', 'قرار فصل'),
    ('dismissal_order_article_41A3', 'قرار فصل مادة 41 ا 3'),
    ('dismissal_order_article_41B1', 'قرار فصل مادة 41 ب1'),
    ('dismissal_order_article_41B2', 'قرار فصل مادة 41 ب2'),
    ('warning_letter', 'انذار'),
    ('subj_suspension', 'ايقاف عن العمل'),
    ('salary_increment', 'زيادة راتب'),
    ('payment_request', 'طلب دفع'),
    # ('pay_slip', 'قسيمة الراتب'),
]

ARABIC_DAYS = [
    'الاثنين',
    'الثلاثاء',
    'الأربعاء',
    'الخميس',
    'الجمعة',
    'السبت',
    'الأحد',
]


class BoutiqaatReportWizarad(models.TransientModel):
    _name = "boutiqaat.report.wizarad"
    _description = 'Boutiqaat Report'

    name = fields.Selection(REPORT_NAME_SELECTION, string='Report Name')
    name_ar = fields.Selection(REPORT_NAME_SELECTION_AR, string='Report Name (Arabic)')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    print_date = fields.Date(string='Print Date', default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company')
    last_work_date = fields.Date(string='Last Working Date', default=fields.Date.today)
    last_date = fields.Date(string='Last Date')
    end_of_service_date = fields.Date(string='End of Service Date')
    signature = fields.Binary(string='Signature')
    notice_period_start_date = fields.Date(string='Notice Period Start Date')
    notice_period_end_date = fields.Date(string='Notice Period End Date')
    resignation_acceptance_date = fields.Date(string='Resignation Acceptance Date')
    break_from_work_start_date = fields.Date(string='Break from Work Start Date')
    break_from_work_end_date = fields.Date(string='Break from Work End Date')
    warning_date = fields.Date(string='Warning Date')
    dismissal_date = fields.Date(string='Dismissal Date')
    arabic_reason = fields.Char(string='Reason (Arabic)')
    english_reason = fields.Char(string='Reason (English)')
    suspension_date = fields.Date(string='Suspension Date')
    amount = fields.Float(string='Amount')
    increment_date = fields.Date(string='Increment Date')
    payment_method = fields.Char(string='Payment Method')
    cost_center = fields.Char(string='Cost Center')
    title_id = fields.Many2one('hr.title', string='Title')
    employee_sign_id = fields.Many2one('hr.employee', string='Employee for Signature')

    def amount_total_words(self, amount):
        amount_total_words = self.env.user.company_id.currency_id.amount_to_text(amount)
        return amount_total_words

    @api.onchange('name')
    def _onchange_name(self):
        self.name_ar = self.name

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.company_id = self.employee_id.company_id

    def get_arabic_day(self, weekday):
        arabic_day = ARABIC_DAYS[weekday]
        return arabic_day

    def print_report(self):
        self.ensure_one()

        if self.name == 'salary_certificate':
            return self.env.ref('boutiqaat_reports.salary_certificate_report').report_action(self)
        if self.name == 'salary_continous_certificate':
            return self.env.ref('boutiqaat_reports.salary_continous_certificate_report').report_action(self)
        if self.name == 'experience_certificate':
            return self.env.ref('boutiqaat_reports.experience_certificate_report').report_action(self)
        if self.name == 'end_of_service_3_months':
            return self.env.ref('boutiqaat_reports.end_of_service_3_months_report').report_action(self)
        if self.name == 'termination_during_probation_period':
            return self.env.ref('boutiqaat_reports.termination_during_probation_period_report').report_action(self)
        if self.name == 'resignation_during_probation_period':
            return self.env.ref('boutiqaat_reports.resignation_during_probation_period_report').report_action(self)
        if self.name == 'resignation_with_notice_period':
            return self.env.ref('boutiqaat_reports.resignation_with_notice_period_report').report_action(self)
        if self.name == 'resignation_with_out_notice_period':
            return self.env.ref('boutiqaat_reports.resignation_without_notice_period_report').report_action(self)
        if self.name == 'dismissal_order':
            return self.env.ref('boutiqaat_reports.dismissal_order_report').report_action(self)
        if self.name == 'dismissal_order_article_41A3':
            return self.env.ref('boutiqaat_reports.dismissal_order_article_41A3_report').report_action(self)
        if self.name == 'dismissal_order_article_41B1':
            return self.env.ref('boutiqaat_reports.dismissal_order_article_41B1_report').report_action(self)
        if self.name == 'dismissal_order_article_41B2':
            return self.env.ref('boutiqaat_reports.dismissal_order_article_41B2_report').report_action(self)
        if self.name == 'warning_letter':
            return self.env.ref('boutiqaat_reports.warning_letter_report').report_action(self)
        if self.name == 'subj_suspension':
            return self.env.ref('boutiqaat_reports.subj_suspension_report').report_action(self)
        if self.name == 'salary_increment':
            return self.env.ref('boutiqaat_reports.salary_increment_report').report_action(self)
        if self.name == 'payment_request':
            return self.env.ref('boutiqaat_reports.payment_request_report').report_action(self)
