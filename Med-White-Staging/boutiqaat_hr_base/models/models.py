# -*- coding: utf-8 -*-

from odoo import fields, models

CURRENTLY_WITH = [
    ('emp', 'Employee'),
    ('org', 'In Office')
]


class PassportHistory(models.Model):
    _name = 'passport.history'
    _description = 'Password History'

    receiving_date = fields.Date('Receiving Date', required=True)
    returning_date = fields.Date('Returning Date')
    reasons = fields.Text('Reasons')
    employee_id = fields.Many2one('hr.employee', string='Employee')


class EmployeeBenefits(models.Model):
    _name = 'employee.benefits'
    _description = 'Employee Benefits'

    name = fields.Char('Benefits', required=True)
    value = fields.Float("Value")
    employee_id = fields.Many2one('hr.employee', string='Employee')


class EmployeeDocument(models.Model):
    _name = 'employee.document'
    _description = "Employee Documents"

    name = fields.Char('Filename', required=True)
    file = fields.Binary('File Content', required=True)
    article_type_id = fields.Many2one('article.type', string="Attachment Type", required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    history_ids = fields.One2many(
        "employee.document.history", "emp_doc_id", string="History")

    date_last_action = fields.Datetime("Since", related="history_ids.date_last_action")
    currently_with = fields.Selection(CURRENTLY_WITH, string="With", related="history_ids.currently_with")


class EmployeeDocHistory(models.Model):
    _name = 'employee.document.history'
    _description = "Employee Documents History"
    _order = "date_last_action desc"

    emp_doc_id = fields.Many2one("employee.document", string="Employee Document")
    currently_with = fields.Selection(CURRENTLY_WITH, string="With", required=True)
    date_last_action = fields.Datetime("Handover Date", default=fields.Datetime.now)
    reason = fields.Text("Reason", required=True)


class HrAsset(models.Model):
    _name = 'employee.asset'
    _description = "Employee Assets"

    name = fields.Char('Asset Name', required=True)
    date_assigned = fields.Datetime('Date Assigned', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')


class EmpDiscount(models.Model):
    _name = 'emp.discount'
    _description = "Employee Discount"
    _order = "date_payslip desc"

    name = fields.Char("Invoice Reference", required=True, index=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    inv_amount = fields.Float("Invoice Amount")
    date_invoice = fields.Date("Invoice Date", required=True)
    note = fields.Text("Note")
    date_payslip = fields.Date(
        "Payslip Date", required=True, help="System will give discount in this Month Payroll.")
    is_discounted = fields.Boolean("Considered in Payslip ?")

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'The invoice reference must be unique !')
    ]


class AttendanceUploadLog(models.Model):
    _name = 'att.upload.log'
    _description = "Attendance Upload Log"

    name = fields.Char("File Name")
    file = fields.Binary("File")
    skipped_count = fields.Integer("Skipped Lines")
    skipped_text = fields.Text("Skipped Text")
    ignored_count = fields.Integer("Ignored Lines")
    ignored_text = fields.Text("Ignored Text")
    no_emp_count = fields.Integer("Employee Not Found Lines")
    no_emp_text = fields.Text("Employee Not Found Text")
    # skipped_count = fields.Integer("Skipped Lines")
    # skipped_text = fields.Text("Skipped Text")