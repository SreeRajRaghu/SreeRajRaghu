from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PCRTransfer(models.TransientModel):
    _name = 'pcr.transfer'
    _description = "PCR Test Transfer"

    action = fields.Selection([
        ('to_transit', 'Sample Taken to Transit'),
        ('to_in_lab', 'Received to In Lab'),
        ('to_received', 'Sample Taken to Received'),
        ('to_inprogress', 'Lab to Under Process'),
        ('to_confirmed', 'Under Process to Confirmed')], default="to_received")
    line_ids = fields.One2many("pcr.transfer.line", "transfer_id")
    batch_no = fields.Char("Batch No.")

    pcr_result = fields.Selection([
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('equivocal', 'Equivocal'),
        ('rejected', 'Rejected')], string='PCR Result', copy=False, tracking=True)
    assign_all = fields.Boolean("Assign to All")

    @api.constrains('line_ids', 'line_ids.pcr_test_id')
    def validate_all_lines(self):
        test_ids = []
        for line in self.line_ids:
            test = line.pcr_test_id
            if test.id in test_ids:
                raise UserError(_('Duplicate line found `%s`') % (test.name))
            test_ids.append(test.id)

    def action_update(self):
        self.ensure_one()
        if self.action == 'to_transit':
            self.line_ids.mapped('pcr_test_id').action_in_transit()

        if self.action == 'to_in_lab':
            self.line_ids.mapped('pcr_test_id').action_in_lab(self.batch_no)

        if self.action == 'to_received':
            self.line_ids.mapped('pcr_test_id').action_received(self.batch_no)

        if self.action == 'to_inprogress':
            if not self.batch_no:
                raise UserError(_('Batch No. is required in order to make it Under Process.'))
            self.line_ids.mapped('pcr_test_id').action_inprogress(self.batch_no)

        if self.action == 'to_confirmed':
            if self.line_ids.filtered(lambda rec: not rec.pcr_result):
                if not self.pcr_result or not self.assign_all:
                    raise UserError(_('Please Update PCR Results in all lines or set mass result.'))
            # lab_tests = self.line_ids.mapped("pcr_test_id")
            pcr_result = self.pcr_result
            for line in self.line_ids:
                line.pcr_test_id.write({'pcr_result': line.pcr_result or pcr_result})
                line.pcr_test_id.action_confirmed()
            # lab_tests.action_done()

    def action_print_qr(self):
        self.ensure_one()
        records = self.line_ids.mapped('pcr_test_id.appointment_id')
        return self.env.ref('medical_pcr.action_appointment_pcr_qr').report_action(records)

    def action_print_barcode(self):
        self.ensure_one()
        records = self.line_ids.mapped('pcr_test_id.appointment_id')
        return self.env.ref('medical_pcr.action_appointment_pcr_barcode').report_action(records)

    def action_update_result(self):
        if self.assign_all:
            if self.action == 'to_confirmed':
                if not self.pcr_result:
                    raise UserError(_('Please select the PCR Result to update all records.'))
                pcr_result = self.pcr_result
                for line in self.line_ids.filtered(lambda r: not r.pcr_result):
                    line.pcr_result = pcr_result
                    # line.pcr_test_id.write({'pcr_result': line.pcr_result or pcr_result})


class PCR_Transfer_Line(models.TransientModel):
    _name = 'pcr.transfer.line'
    _description = "PCR Transfer Line"

    pcr_test_id = fields.Many2one("medical.pcr.test", string="PCR Test", required=True)
    pcr_qr_code = fields.Char(related="pcr_test_id.pcr_qr_code", readonly=True)
    partner_id = fields.Many2one(related="pcr_test_id.partner_id", readonly=True)
    civil_code = fields.Char(related="pcr_test_id.partner_id.civil_code", readonly=True)
    batch_no = fields.Char(related="pcr_test_id.batch_no")
    transfer_id = fields.Many2one("pcr.transfer", string="PCR Transfer")
    action = fields.Selection(related="transfer_id.action")

    pcr_result = fields.Selection([
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('equivocal', 'Equivocal'),
        ('rejected', 'Rejected')], string='PCR Result', copy=False, tracking=True)

    @api.onchange("pcr_test_id")
    def onchange_pcr_result(self):
        if self.pcr_test_id and self.action == 'to_confirmed':
            self.pcr_result = self.pcr_test_id.pcr_result
