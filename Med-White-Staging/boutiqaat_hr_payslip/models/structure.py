
from odoo import fields, models


class PayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    is_without_attendance = fields.Boolean('Is Without Attendance?')


class PayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    def _default_rot_entry_type(self):
        return self.env.ref('boutiqaat_hr_payslip.hr_work_entry_type_rot', False)

    def _default_wot_entry_type(self):
        return self.env.ref('boutiqaat_hr_payslip.hr_work_entry_type_wot', False)

    def _default_pot_entry_type(self):
        return self.env.ref('boutiqaat_hr_payslip.hr_work_entry_type_pot', False)

    def _default_got_entry_type(self):
        return self.env.ref('hr_payroll.work_entry_type_leave', False)

    def_rot_work_entry_type_id = fields.Many2one(
        "hr.work.entry.type", string="Regular OT Work Entry Type",
        default=_default_rot_entry_type)
    def_wot_work_entry_type_id = fields.Many2one(
        "hr.work.entry.type", string="Week Off OT Work Entry Type",
        default=_default_wot_entry_type)
    def_pot_work_entry_type_id = fields.Many2one(
        "hr.work.entry.type", string="Public Holiday OT Work Entry Type",
        default=_default_pot_entry_type)
    def_got_work_entry_type_id = fields.Many2one(
        "hr.work.entry.type", string="Global Holiday OT Work Entry Type",
        default=_default_got_entry_type)
