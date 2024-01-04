from odoo import models
import logging


class MedOrder(models.Model):
    _inherit = "medical.order"

    def send_by_sms(self):
        if self.config_id.company_code:
            sms_config = self.env['sms.config'].sudo().search([('company_code','=',self.config_id.company_code)], limit=1)
        else:
            sms_config = self.env['sms.config'].sudo().search([], limit=1)
        if self.config_id.company_code == 'lab_medgray':
            msg_template = self.env['sms.sms.template'].sudo().search([('code', '=', 'MGL')], limit=1)
        else:
            msg_template = self.env['sms.sms.template'].sudo().search([('code', '=', 'PLT')], limit=1)
        if sms_config and msg_template:
            WSMSConfig = self.env['wizard.sms.send'].sudo()
            sms_vals = {}
            recipients = self.partner_id.phone or self.partner_id.mobile
            if not recipients:
                return
            try:
                msg = msg_template.sudo().render([self.id])[self.id]
                sms_vals = {
                    'config_id': sms_config.id,
                    'contact_list': recipients,
                    'keep_sms_history': True,
                    'message': msg,
                    'language': msg_template.language,
                }
                wizard = WSMSConfig.sudo().create(sms_vals)
                logging.info("SMS: Sending:  %s - %s \n %s" % (self.name, recipients, sms_vals))
                wizard.sudo().send_sms()
                # self.write({'sms_sent': True})
                self.sudo().message_post(body=msg)
                return {'success': True}
            except Exception as e:
                logging.error("ERROR: Appointment: Send SMS %s - %s \n %s" % (self.name, sms_vals, str(e)))
                return {'error': str(e)}

    def send_by_email(self):
        try:
            if not self.partner_id.email:
                return {'error': 'Email is not set on patient.'}

            template = self.env['mail.template'].sudo().search([('name', '=', 'Lab Test Result')], limit=1)
            template.sudo().send_mail(self.id, notif_layout='mail.mail_notification_light', force_send=True)
            return {'success': True}
        except Exception as e:
            logging.error("ERROR: Appointment: Send Email %s" % (str(e)))
            return {'error': str(e)}
