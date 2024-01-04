# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.medical_js.controllers.medical import JS_PARTNER_FIELDS


class ResPartner(models.Model):
    _inherit = 'res.partner'

    prepaid_card_ids = fields.One2many("partner.prepaid.card", "partner_id", string="Prepaid Cards")
    # is_doctor = fields.Boolean("Is Doctor ?")
    medical_resource_ids = fields.One2many("medical.resource", "partner_id", string="Medical Resource")
    has_med_resource = fields.Boolean("Has Resource", compute="_compute_has_med_resource")
    passport_name = fields.Char("Passport Name")
    insurance_start_date = fields.Date('Insurance start date')
    insurance_end_date = fields.Date('Insurance end date')

    @api.onchange('insurance_end_date')
    def onchange_end_date(self):
        if self.insurance_start_date and self.insurance_end_date:
            if self.insurance_start_date >= self.insurance_end_date:
                raise UserError(_('End date should be greater than Start Date'))

    def _compute_has_med_resource(self):
        for rec in self:
            rec.has_med_resource = len(rec.medical_resource_ids.ids) > 0

    def create_med_resource(self):
        self.ensure_one()
        if not self.medical_resource_ids:
            self.env['medical.resource'].create({
                'name': self.name,
                'resource_type': 'free',
                'partner_id': self.id,
                'clinic_name': self.parent_id.name,
            })

    def create_prepaid_card(self):
        self.ensure_one()
        if self.prepaid_card_ids:
            raise UserError(_("Prepaid Card already generated."))
        self.prepaid_card_ids.create({"partner_id": self.id})

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'quick_load_limit' in self.env.context:
            limit = self.env.context['quick_load_limit'] or limit
        return super(ResPartner, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def create_from_medical_ui(self, partner):
        if partner.get('image_1920'):
            partner['image_1920'] = partner['image_1920'].split(',')[1]
        partner_id = partner.pop('id', False)
        if partner_id:
            record = self.browse(partner_id)
            record.write(partner)
        else:
            # partner['lang'] = self.env.user.lang
            record = self.create(partner)
        return record.read(JS_PARTNER_FIELDS)[0] if record else {}

    @api.model
    def remove_attachment(self, attachment_id):
        attachment = self.env['medical.patient.attachment'].browse(attachment_id)
        attachment.ir_attachment_id.unlink()
        attachment.unlink()
        return True

    @api.model
    def upload_attachment(self, vals):
        attachment = self.env['ir.attachment'].create({
                'name': vals.get('name'),
                'datas': vals.get('data'),
                'res_model': 'res.partner',
                'res_id': vals.get('partner_id')
            })
        medi_attach = self.env['medical.patient.attachment'].create({
                'name': attachment.name,
                'ir_attachment_id': attachment.id,
                'partner_id': attachment.res_id,
                'attachment_type_id': vals.get('attachment_type')
            })
        return medi_attach.read(['id', 'name', 'ir_attachment_id', 'attachment_type_id'])


class WorkingSchedule(models.Model):
    _inherit = 'resource.calendar.attendance'

    branch_id = fields.Many2one("medical.clinic", string="Branch")
