from odoo import http
from odoo.http import request
from odoo.osv.expression import AND
import logging
_logger = logging.getLogger(__name__)


class MedicalController(http.Controller):

    @http.route('/medical/web', type='http', auth='user')
    def medical_web(self, config_id=False, **kw):
        domain = [
            ('state', '=', 'opened'),
            ('user_id', '=', request.session.uid),
        ]
        if config_id:
            try:
                domain = AND([domain, [('config_id', '=', int(config_id))]])
            except:
                return 'Invalid Operation, Kindly check scheduler. (Invalid config_id)'
        medical_session = request.env['medical.session'].sudo().search(domain, limit=1)
        medical = request.env['medical.config'].sudo()
        if medical_session:
            medical = medical_session.config_id
            if not config_id:
                config_id = medical_session.config_id.id

        if not medical and config_id:
            medical = medical.search([('id', '=', config_id)], limit=1)

        # print ('___ Opening session medical_session, medical : ', medical_session, medical)
        _logger.info("Opening session : %s, %s by %s,%s ", medical, medical_session, request.env.uid, request.env.user.name)
        if not medical_session:
            return 'Session Not Found. Please Re-Open.'

        session_info = request.env['ir.http'].session_info()
        session_info['user_context']['allowed_company_ids'] = medical.company_id.ids
        context = {
            'session_info': session_info,
            'login_number': medical_session.login(),
            'config_id': config_id,
        }
        context = {
            'session_info': session_info,
        }
        return request.render('medical_js.index', qcontext=context)
