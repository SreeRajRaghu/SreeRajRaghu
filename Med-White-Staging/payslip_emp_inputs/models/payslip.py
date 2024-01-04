from odoo import fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    emp_input_line_ids = fields.One2many(
        "emp.input.line", "payslip_id", string="Emp. Input Lines")

    def action_payslip_done(self):
        super(Payslip, self).action_payslip_done()
        uid = self.env.uid
        cr = self.env.cr
        for payslip in self:
            input_lines = payslip.emp_input_line_ids
            if input_lines:
                sql = """
                    UPDATE emp_input_line
                        SET state='paid', write_uid = %s, write_date=NOW()
                        WHERE id IN %s
                    """
                cr.execute(sql, ((uid, tuple(input_lines.ids))))

                sql = """
                    SELECT emp_input_id, state FROM emp_input_line
                        WHERE emp_input_id IN %s
                    """
                cr.execute(sql, (tuple(input_lines.mapped('emp_input_id.id')),))
                result = cr.fetchall()

                by_emp_input = {}
                for line in result:
                    by_emp_input.setdefault(line[0], [])
                    by_emp_input[line[0]].append(line[1])

                EmpInput = self.env['emp.inputs']

                for k, v in by_emp_input.items():
                    if ['paid'] == list(set(v)):
                        EmpInput.browse(k).action_paid()
