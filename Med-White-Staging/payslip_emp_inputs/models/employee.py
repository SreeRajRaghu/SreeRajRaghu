
from odoo import api, fields, models


class Employee(models.Model):
    _inherit = 'hr.employee'

    emp_input_ids = fields.One2many("emp.inputs", "employee_id", string="Payslip Inputs")
    emp_input_tot_amount = fields.Float("Total Amount", compute="_compute_emp_other_inputs")
    emp_input_amount_unpaid = fields.Float("Unpaid Amount", compute="_compute_emp_other_inputs")

    @api.depends('emp_input_ids', 'emp_input_ids.state', 'emp_input_ids.tot_amount', 'emp_input_ids.amount_unpaid')
    def _compute_emp_other_inputs(self):
        for rec in self:
            other_inputs = rec.emp_input_ids.filtered(lambda inp: inp.state == 'confirm')
            rec.emp_input_tot_amount = sum(other_inputs.mapped('tot_amount'))
            rec.emp_input_amount_unpaid = sum(other_inputs.mapped('amount_unpaid'))

    def get_emp_input_lines(self, date_from, date_to, input_type):
        sql = """
        SELECT l.id, l.amount
        FROM emp_inputs AS input
            LEFT JOIN emp_input_line AS l
                ON l.emp_input_id = input.id
        WHERE
            input.state = 'confirm'
            AND
            input.input_type = %s
            AND
            input.employee_id = %s
            AND
            l.payslip_date BETWEEN %s AND %s
            AND
            l.state = 'due'
            """
        self.env.cr.execute(sql, (
            (input_type, self.id, date_from, date_to)))
        return self.env.cr.fetchall()

    def get_emp_inputs(self, payslip, input_type):
        if not payslip:
            return 0
        total = 0
        result = self.get_emp_input_lines(payslip.date_from, payslip.date_to, input_type)
        if result and payslip.id:
            cr = self.env.cr
            for line in result:
                sql = """
                UPDATE emp_input_line
                    SET payslip_id = %s, write_uid = %s, write_date=NOW()
                    WHERE id = %s
                """
                cr.execute(sql, ((payslip.id, self.env.uid, line[0])))
                total += line[1]
        return total
