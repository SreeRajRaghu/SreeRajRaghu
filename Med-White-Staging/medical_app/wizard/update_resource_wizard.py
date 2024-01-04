# -*- coding: utf-8 -*-

from odoo import fields, models


class UpdateResource(models.TransientModel):
    _name = 'update.resource'
    _description = "Update Resource "

    def _default_appointment(self):
        return self.env['medical.order'].browse(self.env.context.get('active_id'))

    appoinment_id = fields.Many2one(
        'medical.order', string="Appoinment", default=_default_appointment, readonly=True)
    update_resource_id = fields.Many2one('medical.resource', string="Resource", required=True)

    def update_resource(self):
        new_res_id = self.update_resource_id.id
        self.appoinment_id.resource_id = new_res_id

        if self.appoinment_id.patient_invoice_id:
            self.appoinment_id.patient_invoice_id.write({'resource_id': new_res_id})

        if self.appoinment_id.insurance_invoice_id:
            self.appoinment_id.insurance_invoice_id.write({'resource_id': new_res_id})
