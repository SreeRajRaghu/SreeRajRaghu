
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MedicalOrder(models.Model):
    _inherit = "medical.order"

    lab_test_count = fields.Integer(
        compute='_compute_lab_test_count', default=0, string='# Lab Tests')
    medical_lab_test_ids = fields.One2many(
        'medical.lab.test', 'appointment_id', string="Medical Lab Tests")

    def _check_same_test_exists(self):
        if self.env.context.get('ignore_check_case'):
            return
        for rec in self:
            test_ids = []
            for line in rec.line_ids.filtered('product_id.medical_labtest_types_ids'):
                prod_test_ids = line.product_id.medical_labtest_types_ids.ids
                if prod_test_ids:
                    if set(prod_test_ids) & set(test_ids):
                        raise UserError(_('Same Test exist in %s.') % (line.product_id.name))
                    else:
                        test_ids += prod_test_ids
            # for line in rec.line_ids.filtered('product_id.medical_labtest_types_ids'):
            #     cases = []
            #     for lab_test in line.product_id.medical_labtest_types_ids:
            #         this_cases = lab_test.mapped('lab_criteria_ids').filtered(lambda t: not t.display_type).mapped('case_id')
            #         if this_cases:
            #             remain = set(this_cases) & set(cases)
            #             if remain:
            #                 raise UserError(_('Case (%s) exist in service (%s) and lab test (%s).') % (
            #                     ', '.join(list(map(lambda c: c.name, remain))), line.product_id.name, lab_test.name))
            #             else:
            #                 cases += this_cases

    def write(self, vals):
        res = super(MedicalOrder, self).write(vals)
        self._check_same_test_exists()
        return res

    @api.model
    def create(self, vals):
        record = super(MedicalOrder, self).create(vals)
        record._check_same_test_exists()
        return record

    def _compute_lab_test_count(self):
        for rec in self:
            rec.lab_test_count = len(rec.medical_lab_test_ids.ids)

    def create_lab_test(self):
        LabTest = self.env['medical.lab.test']
        lines = self.line_ids.filtered(lambda l: l.product_id.medical_labtest_types_ids and not l.medical_lab_test_ids)
        Sequence = self.env['ir.sequence']

        barcode_dict = {}
        for line in lines:
            for lab_test in line.product_id.medical_labtest_types_ids:
                name = None
                if lab_test.sample_type_id:
                    name = barcode_dict.get(lab_test.sample_type_id.id)
                    if not name:
                        new_seq = Sequence.next_by_code('medical.lab.test')
                        barcode_dict.update({lab_test.sample_type_id.id: new_seq})
                        name = new_seq
                vals = {
                    'name': name,
                    'lab_department_id': lab_test.lab_department_id.id,
                    'test_type_id': lab_test.id,
                    'appointment_id': line.order_id.id,
                    'appointment_line_id': line.id,
                    'partner_id': self.partner_id.id,
                    'resource_id': self.resource_id.id,
                }
                LabTest.create(vals)
        return True

    def action_validate(self):
        record = super(MedicalOrder, self).action_validate()
        self.create_lab_test()
        return record


class MedicalOrderLine(models.Model):
    _inherit = "medical.order.line"

    medical_lab_test_ids = fields.One2many(
        'medical.lab.test', 'appointment_line_id', string="Medical Lab Test", domain=[('state', '!=', 'cancelled')])
    lab_test_status = fields.Char(compute="_compute_is_test_done")

    def _compute_is_test_done(self):
        for rec in self:
            lab_test_status = 'N/A'
            tests = rec.medical_lab_test_ids.filtered(lambda r: r.state != 'cancelled')
            if tests:
                if len(tests.ids) == 1:
                    lab_test_status = tests[0].state
                else:
                    lab_test_status = "Draft"
                    all_states = set(tests.mapped('state'))
                    if 'inprogress' in all_states:
                        lab_test_status = "In Progress"
                    elif all_states == set(['completed']):
                        lab_test_status = "Completed"
                    elif all_states == set(['handover']):
                        lab_test_status = "Hand Over"
            rec.lab_test_status = lab_test_status
