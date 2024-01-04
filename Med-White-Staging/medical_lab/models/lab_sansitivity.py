
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LabSansitivity(models.Model):
    _name = 'lab.sansitivity'
    _description = 'Lab Test sansitivity'

    name = fields.Char(string='Name', required=True)


class LabTestother(models.Model):
    _name = 'lab.test.resistant'
    _description = 'lab test resistant'
    _rec_name = "sensitivity_id"

    result = fields.Char(string='Result')
    sensitivity_id = fields.Many2one('lab.sansitivity', string='Sensitivity')
    medical_lab_test_id = fields.Many2one('medical.lab.test', string='Lab Tests')


class LabTestSens(models.Model):
    _name = 'lab.test.sensitivity'
    _description = 'lab test resistant'
    _rec_name = "sensitivity_id"

    result = fields.Char(string='Result')
    sensitivity_id = fields.Many2one('lab.sansitivity', string='Sensitivity')
    medical_lab_test_id = fields.Many2one('medical.lab.test', string='Lab Tests')


class LabTemplate(models.Model):
    _name = 'lab.template'
    _description = 'lab template'

    name = fields.Char(string='Name', required=True)
    template = fields.Html("Template")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)


class LabTestInter(models.Model):
    _name = 'lab.test.intermediate'
    _description = 'lab test intermediate'
    # _rec_name = "sensitivity_id"

    sensitivity_id = fields.Many2one('lab.sansitivity', string='Sensitivity')
    intermediate_id = fields.Many2one('lab.sansitivity', string='Intermediate')
    resistant_id = fields.Many2one('lab.sansitivity', string='Resistant')
    medical_lab_test_id = fields.Many2one('medical.lab.test', string='Lab Tests')

    @api.constrains('sensitivity_id', 'intermediate_id', 'resistant_id')
    def check_serverity(self):
        for rec in self:
            if rec.sensitivity_id.id and rec.sensitivity_id.id in [rec.intermediate_id.id, rec.resistant_id.id]:
                raise UserError(_('Same `%s` not allowed in Intermediate or Resistant.') % (rec.sensitivity_id.name))
            if rec.intermediate_id.id and rec.intermediate_id.id in [rec.sensitivity_id.id, rec.resistant_id.id]:
                raise UserError(_('Same `%s` not allowed in Sensitivity or Resistant.') % (rec.intermediate_id.name))
            if rec.resistant_id.id and rec.resistant_id.id in [rec.sensitivity_id.id, rec.intermediate_id.id]:
                raise UserError(_('Same `%s` not allowed in Sensitivity or Intermediate.') % (rec.resistant_id.name))
