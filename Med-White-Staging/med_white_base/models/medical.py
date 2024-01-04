# -*- coding: utf-8 -*-

from odoo import api, models
import logging


class MedOrder(models.Model):
    _inherit = "medical.order"

    def send_new_app_sms(self, vals):
        if vals.get('send_sms'):
            sms_config = self.env['sms.config'].search([('company_code', 'in', self.mapped('company_code'))], limit=1)
            msg_template = self.env['sms.sms.template'].search([('code', '=', 'NEW_APP')], limit=1)
            logging.info("SMS: New App : %s %s %s", sms_config, msg_template, self.filtered(lambda o: not o.sms_sent))
            if sms_config and msg_template:
                WSMSConfig = self.env['wizard.sms.send']
                for rec in self.filtered(lambda o: not o.sms_sent):
                    sms_vals = {}
                    recipients = rec.partner_id.phone or rec.partner_id.mobile
                    if not recipients:
                        continue
                    try:
                        msg = msg_template.render([rec.id])[rec.id]
                        sms_vals = {
                            'config_id': sms_config.id,
                            'contact_list': recipients,
                            'keep_sms_history': True,
                            'message': msg,
                            'language': msg_template.language,
                            # 'res_id': rec.id,
                            # 'notif_trigger_id': self.id,
                        }
                        wizard = WSMSConfig.create(sms_vals)
                        logging.info("SMS: Sending:  %s - %s \n %s" % (rec.name, recipients, sms_vals))
                        wizard.send_sms()
                        rec.write({'sms_sent': True})
                        rec.message_post(body=msg)
                    except Exception as e:
                        logging.error("ERROR: Appointment: Send SMS %s - %s \n %s" % (rec.name, sms_vals, str(e)))

    def write(self, vals):
        res = super(MedOrder, self).write(vals)
        self.send_new_app_sms(vals)
        return res

    @api.model
    def create(self, vals):
        record = super(MedOrder, self).create(vals)
        record.send_new_app_sms(vals)
        return record
