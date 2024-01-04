
from odoo import fields, models


class WizMultiCase(models.TransientModel):
    _name = "wiz.multi.case"
    _description = "Wizard Multi Case"

    test_type_id = fields.Many2one("medical.labtest.types", required=True, readonly=True)
    case_ids = fields.Many2many("medical.labtest.case")
    test_ids = fields.Many2many("medical.labtest.types", string="Lab Tests", help="It will copy all cases from selected tests to this test.")

    def add_multi_cases(self):
        Critarea = self.env['medical.labtest.criteria']

        # To Manage the correct sequence
        seq = 0
        for test in self.test_ids:
            for critarea in test.lab_criteria_ids:
                seq += 1
                case = critarea.case_id
                Critarea.create({
                    'sequence': seq,
                    'case_id': case.id,
                    'name': case.name,
                    'unit_id': case.unit_id.id,
                    'medical_type_id': self.test_type_id.id
                })

        for case in self.case_ids:
            seq += 1
            Critarea.create({
                'sequence': seq,
                'case_id': case.id,
                'name': case.name,
                'unit_id': case.unit_id.id,
                'medical_type_id': self.test_type_id.id
            })
