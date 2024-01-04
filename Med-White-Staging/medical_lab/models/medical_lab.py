
from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError

DAYS_IN_YEAR = 360


class LabTestUnits(models.Model):
    _name = 'medical.lab.units'
    _description = 'Lab Test Units'

    name = fields.Char(string='Unit Name', required=True)
    code = fields.Char(string='Code', required=True)

    _sql_constraints = [('name_uniq', 'unique(name)', 'The Lab unit name must be unique')]


class LabTestDepartment(models.Model):
    _name = 'medical.labtest.department'
    _description = 'Lab Test Departments'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)


class LabTestCaseItem(models.Model):
    _name = 'medical.case.range'
    _description = "Medical Case Range"

    name = fields.Text(string='Normal Range', required=True)
    gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female'), ('both', 'Both')], default='both', required=True)
    min_range = fields.Float("Min. Range")
    max_range = fields.Float("Max. Range")
    min_age = fields.Float("Min. Age (Days)")
    max_age = fields.Float("Max. Age (Days)")

    case_id = fields.Many2one("medical.labtest.case", string="Case")


class LabTestCase(models.Model):
    _name = 'medical.labtest.case'
    _description = "medical.labtest.case"

    name = fields.Text(string='Tests', required=True)
    unit_id = fields.Many2one('medical.lab.units', string='Units')
    range_ids = fields.One2many("medical.case.range", "case_id", string="Ranges")
    auto_compute = fields.Boolean(string="Auto Compute Result", default=True)

    def get_related_ranges(self, age_in_year, gender='both'):
        Range = self.env['medical.case.range']
        if not self.exists():
            return Range

        age_in_days = age_in_year * DAYS_IN_YEAR

        domain = [
            ('id', 'in', self.range_ids.ids),
            ('min_age', '<=', age_in_days), ('max_age', '>=', age_in_days)]

        if gender != 'both':
            domain += [('gender', 'in', [gender, 'both'])]
        return Range.search(domain)


class SampleType(models.Model):
    _name = 'test.sample.type'
    _description = 'Test Sample Type'

    name = fields.Char(required=True)

    _sql_constraints = [('name_uniq', 'unique(name)', 'Sample Type name must be unique')]


class LabTestCriteria(models.Model):
    _name = 'medical.labtest.criteria'
    _description = 'Lab Test Criteria'
    _order = "sequence"
    _rec_name = 'case_id'

    # name = fields.Char(string='Criteria')
    case_id = fields.Many2one('medical.labtest.case', string='Tests')
    # normal_range = fields.Text(string='Normal Range', related="case_id.normal_range")
    unit_id = fields.Many2one('medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    medical_type_id = fields.Many2one('medical.labtest.types', string='Lab Test Types')
    display_type = fields.Selection(
        [('line_section', "Section")],
        default=False, help="Technical field for UX purpose.")
    name = fields.Text('Description')
    hide_unit_ref = fields.Boolean("Report: Show Full Line ?")
    # split_page = fields.Boolean("Report: Split Page ?")

    @api.onchange("case_id")
    def onchange_case(self):
        if self.case_id:
            self.unit_id = self.case_id.unit_id
            self.name = self.case_id.name

    @api.model
    def create(self, vals):
        case = False
        if vals.get('case_id'):
            case = self.env['medical.labtest.case'].browse(vals['case_id'])
            vals.update({
                'name': case.name,
            })

        if not vals.get('unit_id') and case:
            vals.update({'unit_id': case.unit_id.id})
        return super(LabTestCriteria, self).create(vals)


class LabTestTypes(models.Model):
    _name = 'medical.labtest.types'
    _description = 'Lab Test Types'

    name = fields.Char(string='Lab Test Name', required=True, help="eg X-Ray, Hemogram, Biopsy...")
    code = fields.Char(string='Code', required=True)
    info = fields.Text(string='Description')
    # test_charge = fields.Float(string='Test Charge', default=lambda *a: 0.0)
    lab_criteria_ids = fields.One2many('medical.labtest.criteria', 'medical_type_id', string='Lab Test Cases')
    lab_department_id = fields.Many2one('medical.labtest.department', string='Department')
    company_id = fields.Many2one(related="lab_department_id.company_id", store=True)

    report_on_full_page = fields.Boolean("Report: Full Page Only")

    sample_type_id = fields.Many2one("test.sample.type", string="Sample Type")

    prod_tmpl_ids = fields.Many2many(
        'product.template', 'labtest_types_product_id', 'product_id', 'labtest_types_id',
        string="Products")
    hide_title = fields.Boolean(string="Report: Hide Header")
    show_service_title = fields.Boolean(string="Report: Show Service Name")


class LabTests(models.Model):
    _name = 'medical.lab.test'
    _description = 'Lab Tests'
    _inherit = ['mail.thread']
    _order = "date_requested desc"

    name = fields.Char(string='Lab Test #', readonly=True, tracking=True)
    lab_department_id = fields.Many2one(
        'medical.labtest.department', string='Department', readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    test_type_id = fields.Many2one(
        'medical.labtest.types', string='Test Type',
        domain="[('lab_department_id', '=', lab_department_id)]",
        required=True, readonly=True, states={'draft': [('readonly', False)]}, help="Lab Test Type", tracking=True)
    company_id = fields.Many2one(related="test_type_id.company_id", store=True)
    company_code = fields.Selection(related="appointment_id.config_id.company_code")

    partner_id = fields.Many2one(
        'res.partner', store=True, string='Patient', help="Patient Name", readonly=True,
        states={'draft': [('readonly', False)]}, tracking=True)
    age_in_days = fields.Integer(compute="_compute_age_in_days", tracking=True)
    file_no = fields.Char(related="partner_id.file_no")
    age = fields.Integer(related="partner_id.age")
    appointment_id = fields.Many2one(
        'medical.order', store=True, string='Appointment',
        readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    appointment_line_id = fields.Many2one(
        'medical.order.line', string='Appointments Line', help="Appointments Line",
        states={'draft': [('readonly', False)]}, readonly=True, tracking=True)
    product_id = fields.Many2one(
        related="appointment_line_id.product_id", store=True, tracking=True, string="Service")
    results = fields.Text(
        string='Comment', readonly=True, states={'draft': [('readonly', False)], 'inprogress': [('readonly', False)]}, tracking=True)
    diagnosis = fields.Text(
        string='Diagnosis', readonly=True, states={'draft': [('readonly', False)], 'inprogress': [('readonly', False)]}, tracking=True)
    lab_test_criteria_ids = fields.One2many(
        'medical.lab.resultcriteria', 'medical_lab_test_id', string='Lab Test Result',
        readonly=True, states={'draft': [('readonly', False)], 'inprogress': [('readonly', False)]}, tracking=True)
    date_requested = fields.Datetime(
        string='Date Requested', readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now, tracking=True)
    date_analysis = fields.Datetime(
        string='Analysis Date ', readonly=True, states={'draft': [('readonly', False)], 'inprogress': [('readonly', False)]}, tracking=True)
    state = fields.Selection([
        ('draft', 'Sample'),
        ('inprogress', 'inprogress'),
        ('hold', 'Hold'),
        ('waiting_result', 'Waiting For Result'),
        ('completed', 'Completed'),
        ('handover', 'Handover'),
        ('cancelled', 'Cancelled'),
    ], string='State', readonly=True, default='draft', tracking=True)

    employee_id = fields.Many2one("hr.employee", string="Technician", tracking=True)
    date_completed = fields.Datetime("Completion Date", tracking=True)

    resource_id = fields.Many2one(
        "medical.resource", string="Ref. Doctor",
        states={'draft': [('readonly', False)]}, readonly=True, tracking=True)
    smpl_code = fields.Char(compute='_compute_smpl_code', string='Sample Code')
    print_history = fields.Boolean("Print History", default=False)

    # sensitivity_ids = fields.One2many('lab.test.sensitivity', 'medical_lab_test_id')
    # resistant_ids = fields.One2many('lab.test.resistant', 'medical_lab_test_id')
    intermediate_ids = fields.One2many('lab.test.intermediate', 'medical_lab_test_id')

    lab_template_id = fields.Many2one('lab.template', string="Lab Template")
    result_content = fields.Html("Result Content")
    result_attachment_ids = fields.Many2many(
        'ir.attachment', 'lab_test_attachments_rel', 'lab_test_id', 'attachment_id', string="Result Attachments", tracking=True)

    @api.onchange("lab_template_id")
    def onchange_template(self):
        if self.lab_template_id.template:
            self.result_content = self.lab_template_id.template

    def _compute_age_in_days(self):
        today = fields.Date.today()
        for rec in self:
            age_in_days = 0
            if rec.partner_id.birthday:
                age_in_days = (today - rec.partner_id.birthday).days
            rec.age_in_days = age_in_days

    def _compute_smpl_code(self):
        for rec in self:
            rec.smpl_code = "%s/%s/%s" % (rec.lab_department_id.code or '', rec.test_type_id.code or '', rec.name or '')

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            sequence = self.env['ir.sequence'].next_by_code('medical.lab.test')
            vals['name'] = sequence or '/NoSequence'
        record = super(LabTests, self).create(vals)
        if not vals.get('resource_id') and vals.get('appointment_id') and record.appointment_id.resource_id:
            record.resource_id = record.appointment_id.resource_id
        return record

    # Fetching lab test types
    # @api.onchange('test_type_id')
    # def onchange_test_type_id(self):
    #     values = self.onchange_test_type_id_values(self.test_type_id.id if self.test_type_id else False)
    #     return values

    @api.onchange('appointment_id')
    def onchange_appointments(self):
        res = {}
        if self.appointment_id:
            if self.appointment_id.partner_id:
                self.partner_id = self.appointment_id.partner_id

            res['domain'] = {
                'appointment_line_id': [('id', 'in', self.appointment_id.line_ids.ids)],
                'partner_id': [('id', 'in', self.appointment_id.partner_id.ids)]
            }
        return res

    def get_patient_result_history(self, lab_tests):
        self.ensure_one()
        test_types = lab_tests.mapped('test_type_id')
        domain = [
            ('date_requested', '!=', False),
            # ('state', 'in', ['completed', 'handover']),
            ('id', 'not in', lab_tests.ids),
            ('partner_id', '=', self.partner_id.id), ('test_type_id', 'in', test_types.ids)]
        history_results = self.search(domain, limit=5)
        result = {'lines': [], 'dates': []}
        if len(history_results.ids) > 0:
            default_cases = {}
            date_list = []
            for rec in history_results:
                dt = rec.date_requested.date()
                date_list.append(dt)
                for line in rec.lab_test_criteria_ids:
                    case_id = line.case_id.id
                    default_cases.setdefault(case_id, {dt: {}, 'case': line.case_id.name, 'dt': dt})
                    result = line.result
                    if result is False:
                        result = ''
                    default_cases[case_id][dt] = {'result': result, 'auto': line.computed_result}
            result = {'lines': default_cases, 'dates': list(set((date_list)))}
        return result

    def action_cancel(self):
        self.mapped('lab_test_criteria_ids').unlink()
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_hold(self):
        self.write({'state': 'hold'})

    def action_waiting_result(self):
        self.write({'state': 'waiting_result'})

    def update_to_handover(self):
        upd_records = self.filtered(lambda r: r.state == 'completed')
        if upd_records:
            upd_records.write({'state': 'handover'})

    def print_patient_labtest(self):
        records = self.filtered(lambda r: r.state in ('completed', 'handover'))
        records.update_to_handover()
        return self.env.ref('medical_lab.action_report_patient_labtest').report_action(records)

    def set_to_test_inprogress(self):
        Critarea = self.env['medical.labtest.criteria']
        for rec in self.filtered(lambda r: r.state == 'draft'):
            partner = rec.partner_id
            if not partner.gender or not rec.age_in_days:
                raise UserError(_('Patient Gender and Age is required before starting the test.'))
            if not rec.test_type_id:
                raise UserError(_("Please select Lab Test"))

            lab_criterias = Critarea.search(
                [('medical_type_id', '=', rec.test_type_id.id)])

            labtest_ids = []
            for item in lab_criterias:
                specs = {
                    'sequence': item.sequence,
                    'case_id': item.case_id.id,
                    'unit_id': item.unit_id.id,
                    'display_type': item.display_type,
                    'name': item.name or item.case_id.name,
                    # 'split_page': item.split_page,
                    'hide_unit_ref': item.hide_unit_ref,
                }
                ranges = item.case_id.get_related_ranges(partner.age, partner.gender)
                if ranges:
                    a_range = ranges[0]
                    specs.update({
                        'case_range_id': a_range.id,
                        'normal_range': a_range.name,
                    })
                labtest_ids += [(0, 0, specs)]

            rec.lab_test_criteria_ids = False
            rec.write({
                'lab_test_criteria_ids': labtest_ids,
                'state': 'inprogress',
                'date_analysis': datetime.datetime.now()
            })

    def set_to_test_complete(self):
        # if self.env.user.has_group('medical_lab.group_medical_manager'):
        #     self.action_complete()
        # else:
        if self.filtered(lambda r: r.state != 'inprogress'):
            raise UserError(_('All tests must be inprogress.'))
        action = self.env.ref('medical_lab.wiz_emp_password_action').read()[0]
        ctx = self.env.context.copy()
        ctx.update({
            'default_test_ids': [(4, _id) for _id in self.ids],
        })
        action.update({
            'context': ctx
        })
        return action

    def action_complete(self, emp_id):
        return self.write({
            'state': 'completed',
            'employee_id': emp_id,
            'date_completed': fields.Datetime.now()
        })

    # def unlink(self):
    #     for labtest in self.filtered(lambda labtest: labtest.state not in ['draft']):
    #         raise UserError(_('You cannot delete a lab test which is not in "draft" state !!'))
    #     return super(LabTests, self).unlink()

    def unlink(self):
        raise UserError(_("Lab Test cannot be deleted, You can cancel it."))

    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id


class LabTestsResultCriteria(models.Model):
    _name = 'medical.lab.resultcriteria'
    _description = 'Lab Test Result Criteria'
    _order = "sequence"
    _rec_name = 'case_id'

    case_id = fields.Many2one('medical.labtest.case', string='Tests')
    auto_compute = fields.Boolean(related="case_id.auto_compute")
    case_range_id = fields.Many2one('medical.case.range', domain="[('case_id','=', case_id)]", string="Case Range")
    result = fields.Text(string='Result')
    normal_range = fields.Text(string='Normal Range')
    unit_id = fields.Many2one('medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    medical_lab_test_id = fields.Many2one('medical.lab.test', string='Lab Tests')
    computed_result = fields.Char(compute="_compute_computed_result", string="Auto Result")
    result_fetched = fields.Boolean(string="Result Fetched")

    display_type = fields.Selection(
        [('line_section', "Section")],
        default=False, help="Technical field for UX purpose.")
    name = fields.Char('Description')
    comment = fields.Text("Comment")
    hide_unit_ref = fields.Boolean("Report: Show Full Line ?")
    # split_page = fields.Boolean("Report: Split Page ?")

    def _compute_computed_result(self):
        for rec in self:
            result = ''
            arange = rec.case_range_id
            if rec.result and rec.case_id.auto_compute and arange:
                try:
                    actual_res = float(rec.result)
                    symbol = ''
                except:
                    symbol = rec.result.strip()[0]
                    actual_res = 0
                    pass
                if actual_res > arange.max_range and not symbol:
                    result = 'H'
                elif actual_res < arange.min_range and not symbol:
                    result = 'L'
                elif symbol and symbol == '>':
                    result = 'H'
                elif symbol and symbol == '<':
                    result = 'L'
                else:
                    result = 'N'
            rec.computed_result = result

    @api.onchange("case_id")
    def onchange_case_id(self):
        if self.case_id:
            self.name = self.case_id.name
            self.unit_id = self.case_id.unit_id.id

    def check_range(self):
        for rec in self.filtered(lambda r: not r.normal_range):
            partner = rec.medical_lab_test_id.partner_id
            if not rec.case_range_id and rec.case_id:
                ranges = rec.case_id.get_related_ranges(partner.age, partner.gender)
                if ranges:
                    a_range = ranges[0]
                    rec.write({'case_range_id': a_range.id, 'normal_range': a_range.name})

    @api.model
    def create(self, vals):
        record = super(LabTestsResultCriteria, self).create(vals)
        record.check_range()
        return record

    def write(self, vals):
        res = super(LabTestsResultCriteria, self).write(vals)
        self.check_range()
        return res
