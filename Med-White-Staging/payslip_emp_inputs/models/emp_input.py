
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EmpInputCateg(models.Model):
    _name = 'emp.input.category'
    _description = "Employee Input Category"

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Given category code already exists."),
    ]

    def unlink(self):
        if self.filtered(lambda r: r.code == 'INP_CATEG_LEAVE'):
            raise UserError(_('You cannot remove system generated category.'))
        return super(EmpInputCateg, self).unlink()


class EmpInput(models.Model):
    _name = 'emp.inputs'
    _description = "Employee Inputs"
    _inherit = ['mail.thread']

    def _default_category(self):
        return self.env['emp.input.category'].search([('code', '=', 'INP_CATEG_LEAVE')], limit=1)

    name = fields.Char("Description", required=True, tracking=100)
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, index=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=100)
    input_type = fields.Selection(
        [("alw", 'Allowance'), ('ded', 'Deduction')],
        required=True, string="Input Type", tracking=100)
    category_id = fields.Many2one(
        "emp.input.category", string="Category", required=True,
        default=_default_category)
    tot_amount = fields.Float("Total Amount", required=True, tracking=100)
    no_of_installment = fields.Integer("Total Installment", required=True, tracking=100)
    installment = fields.Float("Monthly Installment", compute="_compute_installment", store=True, tracking=100)
    start_date = fields.Date("Payslip Start Date", required=True, tracking=100)
    to_date = fields.Date("Upto Payslip Date", compute="_compute_to_date", store=True, tracking=100)

    department_id = fields.Many2one("hr.department", string="Department")
    mobile = fields.Char("Mobile", tracking=100)
    phone = fields.Char("Phone", tracking=100)
    identification_id = fields.Char("Employee Number", tracking=100)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, copy=False, required=True,
        default=lambda self: self.env.company, tracking=100)
    state = fields.Selection([
        ("draft", "Draft"), ("confirm", "Confirmed"), ("paid", "Paid"), ("cancel", "Cancelled")],
        string="State", default="draft", required=True, tracking=100)
    input_line_ids = fields.One2many("emp.input.line", "emp_input_id", string="Employee Input Lines")
    amount_unpaid = fields.Float("Unpaid Amount", compute="_compute_amount_unpaid")

    bulk_input_id = fields.Many2one("bulk.emp.inputs", string="Bulk Input")

    @api.depends("state", "input_line_ids", "to_date")
    def _compute_amount_unpaid(self):
        for rec in self:
            amount = sum(rec.input_line_ids.filtered(lambda r: r.state == 'due').mapped('amount'))
            rec.amount_unpaid = amount

    @api.onchange('employee_id')
    def _onchange_employee(self):
        emp = self.employee_id
        if emp:
            self.department_id = emp.department_id
            self.mobile = emp.mobile_phone
            self.phone = emp.phone
            self.identification_id = emp.identification_id

    @api.depends("no_of_installment", "tot_amount")
    def _compute_installment(self):
        for rec in self.filtered(lambda r: r.tot_amount and r.no_of_installment):
            rec.installment = rec.tot_amount / rec.no_of_installment

    @api.depends("no_of_installment", "start_date")
    def _compute_to_date(self):
        for rec in self.filtered(lambda r: r.tot_amount and r.start_date):
            rec.to_date = rec.start_date + relativedelta(months=1, days=-1)

    def action_confirm(self):
        if not self.env.context.get('no_regular_installment'):
            for rec in self:
                amount = rec.installment
                start_date = rec.start_date
                vals_list = []
                for i in range(0, rec.no_of_installment):
                    vals_list.append({
                        'amount': amount,
                        'payslip_date': start_date + relativedelta(months=i),
                        'emp_input_id': rec.id,
                    })
                rec.input_line_ids.create(vals_list)
        self.write({"state": "confirm"})

    def action_cancel(self):
        if self.mapped('input_line_ids').filtered(lambda l: l.state == 'paid'):
            raise UserError(_("You cannot cancel Input Lines which are paid."))
        self.mapped('input_line_ids').unlink()
        self.write({"state": "cancel"})

    def action_reset(self):
        self.write({"state": "draft"})

    def action_paid(self):
        self.write({"state": "paid"})

    def open_lines(self):
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'emp.input.line',
            'domain': [('emp_input_id', '=', self.ids)]
        }

    def unlink(self):
        input_lines = self.mapped('input_line_ids')
        if input_lines and input_lines.mapped('payslip_id') and input_lines.filtered(lambda r: r.state != 'due'):
            raise UserError(_('You cannot remove this Input due to Payslip is Linked and Confirmed.'))
        return super(EmpInput, self).unlink()


class EmpInputLine(models.Model):
    _name = 'emp.input.line'
    _description = "Employee Input Lines"
    _rec_name = 'payslip_date'
    _order = 'payslip_date'

    payslip_date = fields.Date("Payslip Date", required=True)
    amount = fields.Float("Amount", required=True)
    emp_input_id = fields.Many2one("emp.inputs", "Employee Input")
    state = fields.Selection([("due", 'Due'), ("paid", "Paid")], string="State", default="due")
    payslip_id = fields.Many2one("hr.payslip", string="Payslip")
    categ_code = fields.Char(related="emp_input_id.category_id.code", store=True)
