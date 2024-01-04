
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class EmpInput(models.Model):
    _name = 'bulk.emp.inputs'
    _description = "Bulk Employee Inputs"

    name = fields.Char("Bulk Description", required=True)

    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, copy=False,
        default=lambda self: self.env.company)
    employee_ids = fields.Many2many(
        "hr.employee", string="Employees", required=True, domain=None)
    input_type = fields.Selection(
        [("alw", 'Allowance'), ('ded', 'Deduction')],
        required=True, string="Input Type")
    category_id = fields.Many2one(
        "emp.input.category", string="Category", required=True)
    start_date = fields.Date("Payslip Start Date", required=True)
    to_date = fields.Date("Upto Payslip Date", compute="_compute_to_date", store=True)

    tot_amount = fields.Float("Total Amount", required=True)
    no_of_installment = fields.Integer("Total Installment", required=True)
    installment = fields.Float("Monthly Installment", compute="_compute_installment", store=True)

    input_ids = fields.One2many("emp.inputs", "bulk_input_id", string="Emp. Input")
    state = fields.Selection([
        ("draft", "Draft"), ("confirm", "Confirmed"), ("cancel", "Cancelled")],
        string="State", default="draft", required=True)

    @api.depends("no_of_installment", "tot_amount")
    def _compute_installment(self):
        for rec in self.filtered(lambda r: r.tot_amount and r.no_of_installment):
            rec.installment = rec.tot_amount / rec.no_of_installment

    @api.depends("no_of_installment", "start_date")
    def _compute_to_date(self):
        for rec in self.filtered(lambda r: r.tot_amount and r.start_date):
            rec.to_date = rec.start_date + relativedelta(day=1, months=1, days=-1)

    def action_prepare_lines(self):
        self.ensure_one()
        EmpInput = self.env['emp.inputs']
        for emp in self.employee_ids:

            existing_rec = EmpInput.search([
                ('employee_id', '=', emp.id),
                ('bulk_input_id', '=', self.id)])

            vals = {
                'name': self.name,
                'input_type': self.input_type,
                'start_date': self.start_date,
                'tot_amount': self.tot_amount,
                'category_id': self.category_id.id,
                'no_of_installment': self.no_of_installment,
            }
            if existing_rec:
                existing_rec.write(vals)
            else:
                vals.update({
                    'employee_id': emp.id,
                    'bulk_input_id': self.id,
                })
                EmpInput.create(vals)

    def action_confirm(self):
        self.input_ids.action_confirm()
        self.write({'state': 'confirm'})

    def action_cancel(self):
        self.input_ids.action_cancel()
        self.write({'state': 'cancel'})

    def action_reset(self):
        self.write({'state': 'draft'})


# class EmpInputLine(models.Model):
#     _name = 'bulk.input.line'
#     _description = "Bulk Input Line"

# access_bulk_input_line,access_bulk_input_line,model_bulk_input_line,base.group_user,1,1,1,1
