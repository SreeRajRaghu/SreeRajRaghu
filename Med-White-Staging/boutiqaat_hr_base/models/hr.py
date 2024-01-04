# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Employee(models.Model):
    _inherit = "hr.employee"

    job_pos_permit_id = fields.Many2one('hr.job', string='Position In Work Permit')
    social_media_account = fields.Char('Social Media Account')

    emp_asset_ids = fields.One2many("employee.asset", "employee_id", string="Assets")
    emp_asset_count = fields.Integer("Total Assets", compute="_compute_asset_count")

    passpory_history_ids = fields.One2many('passport.history', 'employee_id', string='Passpory History')
    benefits_ids = fields.One2many('employee.benefits', 'employee_id', string='Benefits')
    exit_interview = fields.Char('Exit Interview')

    file_ids = fields.One2many('employee.document', 'employee_id', string='Files')
    file_count = fields.Integer("Total Files", compute="_compute_file_count")

    arabic_name = fields.Char('Arabic Name')
    section_id = fields.Many2one('hr.section', string='Section')
    work_address = fields.Char('Work Address')
    private_address = fields.Char("Private Address")
    company_assets = fields.Char("Company Assets")
    certificate_level = fields.Char('Certificate Level')
    grade_id = fields.Many2one('hr.grade', string='Grade')
    is_completed_hajj = fields.Boolean('Is Completed Hajj ?', readonly=True)
    sick_leave_days_in_cur_year = fields.Float(compute='_get_sick_leaves', string='Sick Leaves for Current Year')
    inv_discount_ids = fields.One2many("emp.discount", "employee_id", string="Invoice Discounts")

    bank_id = fields.Many2one("res.bank", string="Bank")
    bank_number = fields.Char('Bank Number')
    iban_number = fields.Char("IBAN")
    pay_through = fields.Selection([
        ('bank', 'Bank'),
        ('cash', 'Cash'),
        ('other', 'Other')],
        default='bank', string="Pay Through")
    identification_id = fields.Char("Employee Number")

    # Inherited

    gender = fields.Selection(groups="")
    marital = fields.Selection(groups="")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += ['|', '|', ('identification_id', 'ilike', name), ('work_phone', 'ilike', name)]
        return super(Employee, self).name_search(name=name, args=args, operator=operator, limit=limit)

    def name_get(self):
        result = super(Employee, self).name_get()
        if self.ids:
            sql = "SELECT id, identification_id FROM hr_employee WHERE id IN %s"
            self.env.cr.execute(sql, (tuple(self.ids),))
            result_identity = self.env.cr.fetchall()
            if result_identity:
                new_result = []
                result_identity = dict(result_identity)
                for _id, name in result:
                    identity = result_identity.get(_id) or ""
                    identity = "[%s] " % identity if identity else ""
                    new_result.append((_id, "%s %s" % (identity, name)))
                return new_result
        return result

    def _get_sick_leaves(self):
        HrLeave = self.env['hr.leave']
        sick_leave = self.env['hr.leave.type'].search([
            ('leave_type', '=', 'sick')], limit=1)
        for emp in self:
            domain = [
                ('holiday_status_id', '=', sick_leave.id),
                ('employee_id', '=', self.id),
                ('state', '=', 'validate'),
            ]
            if sick_leave.validity_start and sick_leave.validity_stop:
                domain.append(('request_date_from', '>=', sick_leave.validity_start))
                domain.append(('request_date_to', '<=', sick_leave.validity_stop))

            leaves = HrLeave.search(domain)
            total_days = 0
            for leave in leaves:
                total_days += (leave.request_date_to - leave.request_date_from).days + 1
            # total_days = sum(leave.number_of_days for leave in leaves)
            emp.sick_leave_days_in_cur_year = total_days

    def _compute_file_count(self):
        for rec in self:
            rec.file_count = len(rec.file_ids.ids)

    def _compute_asset_count(self):
        for rec in self:
            rec.emp_asset_count = len(rec.emp_asset_ids.ids)

    def get_inv_discount(self, payslip):
        sql = """
        SELECT sum(inv_amount) FROM emp_discount
        WHERE employee_id = %s AND date_payslip BETWEEN %s AND %s
        """
        self.env.cr.execute(sql, (self.id, payslip.date_from, payslip.date_to))
        result = self.env.cr.fetchone()
        if result:
            return result[0] or 0
        return 0

    def get_loan_deduction(self, date_from, date_to):
        sql = """
        SELECT sum(line.amount)
        FROM hr_loan_line AS line LEFT JOIN
            hr_loan AS loan ON loan.id = line.loan_id
        WHERE loan.employee_id = %s AND line.date BETWEEN %s AND %s
        """
        self.env.cr.execute(sql, (self.id, date_from, date_to))
        result = self.env.cr.fetchone()
        return result and result[0] or 0

    def get_loan_amount(self, payslip):
        return self.get_loan_deduction(payslip.date_from, payslip.date_to)

    def get_last_holiday(self, date_payslip):
        leave = self.env['hr.leave'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'validate'),
            ('date_from', '<', date_payslip),
            # ('date_to', '>', date_payslip),
        ], order='request_date_from desc', limit=1)
        return leave


class HrSection(models.Model):
    _name = 'hr.section'
    _description = 'Section'

    name = fields.Char('Section', required=True)


class HrGrade(models.Model):
    _name = 'hr.grade'
    _description = 'Grade'

    name = fields.Char('Grade', required=True)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    arabic_name = fields.Char('Arabic Name')


class HrJob(models.Model):
    _inherit = 'hr.job'

    arabic_name = fields.Char('Arabic Name')


class Country(models.Model):
    _inherit = 'res.country'

    arabic_name = fields.Char('Arabic Name')


class Company(models.Model):
    _inherit = 'res.company'

    arabic_name = fields.Char('Arabic Name')
    font = fields.Selection(selection_add=[('Times New Roman', 'Times New Roman')], default="Times New Roman")


class Bank(models.Model):
    _inherit = 'res.bank'

    arabic_name = fields.Char('Arabic Name')


class HrTitle(models.Model):
    _name = 'hr.title'
    _description = "HR Title"

    name = fields.Char('Name', required=True)


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    job_pos_permit_id = fields.Many2one('hr.job', string='Position In Work Permit', readonly=True)
    social_media_account = fields.Char('Social Media Account', readonly=True)

    emp_asset_ids = fields.One2many("employee.asset", "employee_id", string="Assets", readonly=True)
    emp_asset_count = fields.Integer("Total Assets", compute="_compute_asset_count", readonly=True)

    passpory_history_ids = fields.One2many('passport.history', 'employee_id', string='Passpory History', readonly=True)
    benefits_ids = fields.One2many('employee.benefits', 'employee_id', string='Benefits', readonly=True)
    exit_interview = fields.Char('Exit Interview', readonly=True)

    file_ids = fields.One2many('employee.document', 'employee_id', string='Files', readonly=True)
    file_count = fields.Integer("Total Files", compute="_compute_file_count", readonly=True)

    arabic_name = fields.Char('Arabic Name', readonly=True)
    section_id = fields.Many2one('hr.section', string='Section', readonly=True)
    work_address = fields.Char('Work Address', readonly=True)
    private_address = fields.Char("Private Address", readonly=True)
    company_assets = fields.Char("Company Assets", readonly=True)
    certificate_level = fields.Char('Certificate Level', readonly=True)
    grade_id = fields.Many2one('hr.grade', string='Grade', readonly=True)
    is_completed_hajj = fields.Boolean('Is Completed Hajj ?', readonly=True)
    sick_leave_days_in_cur_year = fields.Float(compute='_get_sick_leaves', string='Sick Leaves for Current Year')
    inv_discount_ids = fields.One2many("emp.discount", "employee_id", string="Invoice Discounts", readonly=True)

    bank_id = fields.Many2one("res.bank", string="Bank")
    bank_number = fields.Char('Bank Number')
    iban_number = fields.Char("IBAN")
    pay_through = fields.Selection([
        ('bank', 'Bank'),
        ('cash', 'Cash'),
        ('other', 'Other')],
        default='bank', string="Pay Through")
    identification_id = fields.Char("Employee Number")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], default="male", readonly=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', default='single', readonly=True)
