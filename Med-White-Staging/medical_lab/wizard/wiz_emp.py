
from odoo import fields, models, _
from odoo.exceptions import UserError


class WizEmpPassword(models.TransientModel):
    _name = "wiz.emp.password"
    _description = "Wizard Emp Password"

    employee_id = fields.Many2one('hr.employee', string="Emplyee", required=True)
    password = fields.Char(required=True)
    test_id = fields.Many2one("medical.lab.test", required=False)
    test_ids = fields.Many2many("medical.lab.test")
    msg = fields.Char()

    def check_password(self):
        if self.employee_id.pin == self.password:
            tests = self.test_id | self.test_ids
            tests.action_complete(self.employee_id.id)
        else:
            raise UserError(_("Wrong Password"))


class UpdateResource(models.TransientModel):
    _inherit = 'update.resource'

    def update_resource(self):
        super().update_resource()
        new_res_id = self.update_resource_id.id
        self.appoinment_id.resource_id = new_res_id
        if self.appoinment_id.medical_lab_test_ids:
            self.appoinment_id.medical_lab_test_ids.with_context(
                ignore_check_case=True).write({'resource_id': new_res_id})
