# -*- coding: utf-8 -*-

import time

from odoo import fields, models
from odoo.http import request


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def render_template(self, template, values=None):
        """Allow to render a QWeb template python-side. This function returns the 'ir.ui.view'
        render but embellish it with some variables/methods used in reports.
        :param values: additionnal methods/variables used in the rendering
        :returns: html representation of the template
        """
        if values is None:
            values = {}

        context = dict(self.env.context, inherit_branding=False)

        # Browse the user instead of using the sudo self.env.user
        user = self.env['res.users'].browse(self.env.uid)
        website = None
        if request and hasattr(request, 'website'):
            if request.website is not None:
                website = request.website
                context = dict(context, translatable=context.get('lang') != request.env['ir.http']._get_default_lang().code)

        view_obj = self.env['ir.ui.view'].with_context(context)
        if self.env.context.get('company_id'):
            company_id = self.env.context.get('company_id')
            company = self.env['res.company'].browse(company_id)
        else:
            company = user.company_id
        values.update(
            time=time,
            context_timestamp=lambda t: fields.Datetime.context_timestamp(self.with_context(tz=user.tz), t),
            user=user,
            res_company=company,
            website=website,
            web_base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url', default=''),
        )
        return view_obj.render_template(template, values)
