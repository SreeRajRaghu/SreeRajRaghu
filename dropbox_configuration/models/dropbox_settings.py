import requests
import json
from odoo import models, fields, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
_logger.info("================MODULE===================")
from odoo.addons.dropbox_configuration.dropbox import dbx


class DropboxSetting(models.Model):
    _name = 'dropbox.settings'
    _rec_name = 'company_id'

    company_id = fields.Many2one('res.company')
    dropbox_url = fields.Char('Dropbox URL')
    dropbox_api_key = fields.Char('Dropbox API Key')
    dropbox_secret_key = fields.Char('Dropbox Secret Key')
    dropbox_access_token = fields.Text('Dropbox Access Token')
    dropbox_refresh_token = fields.Char('API Refresh Token')
    message = fields.Char('Message File Path')
    homework = fields.Char('Homework File Path')
    assignment = fields.Char('Assignment File Path')
    timeline = fields.Char('Timeline File Path')

    def test_connection(self):
        connection = self.make_connection()
        if not connection:
            raise ValidationError(_("connection cannot be established"))
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "connection success",
                                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def make_connection(self):
        connection = dbx.connect_dbx(self.dropbox_access_token)
        if not connection:
            response = self.get_access_token()
            if response.get('error'):
                raise ValidationError(_("connection cannot be established"))
            self.dropbox_access_token = response['access_token']
            connection = dbx.connect_dbx(self.dropbox_access_token)
        return connection

    def upload_file(self, raw_data, file_from, file_name):
        path = self[file_from]
        if not path:
            raise ValidationError(_("Path not Defined for %s ") % file_name)
        if not raw_data or not file_name:
            raise ValidationError(_("File or Path not Defined !"))
        dbx_connection = self.make_connection()
        if not dbx_connection:
            raise ValidationError(_("Cannot Establish DBX connection"))
        response = dbx.upload_a_file(dbx_connection, raw_data, path, file_name)
        return response

    def download_file(self, file_id):
        if not file_id:
            raise ValidationError(_("File Id not Defined for %s ") % file_id)
        dbx_connection = self.make_connection()
        if not dbx_connection:
            raise ValidationError(_("Cannot Establish DBX connection"))
        response = dbx.download_file(dbx_connection, file_id)
        return response

    def delete_file(self, file_id):
        if not file_id:
            raise ValidationError(_("Path not Defined for %s ") % file_id)
        dbx_connection = self.make_connection()
        if not dbx_connection:
            raise ValidationError(_("Cannot Establish DBX connection"))
        response = dbx.delete_file(dbx_connection, file_id)
        return response

    def get_access_token(self):
        url = self.dropbox_url + "grant_type=refresh_token&refresh_token=" + self.dropbox_refresh_token +\
              "&client_id=" + self.dropbox_api_key + "&client_secret=" + self.dropbox_secret_key
        response = requests.request("POST", url)
        datas = json.loads(response.text)
        print(response.text)
        return datas

    def is_dbx_dir(self, file_path):
        if not file_path:
            raise ValidationError(_("Path not Defined for"))
        dbx_connection = self.make_connection()
        if not dbx_connection:
            raise ValidationError(_("Cannot Establish DBX connection"))
        response = dbx.is_dir_dbx(dbx_connection, file_path)
        return response
