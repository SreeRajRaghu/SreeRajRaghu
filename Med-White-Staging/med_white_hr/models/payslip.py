from odoo import models, api


class Payslip(models.Model):
    _inherit = "hr.payslip"

    def send_payslip_by_email(self):
        template = self.env.ref('med_white_hr.mail_payslip_by_email', raise_if_not_found=False)
        if template:
            for payslip in self:
                template.sudo().with_context(
                    lang=payslip.employee_id.user_id.partner_id.lang,
                ).send_mail(payslip.id, force_send=True)
