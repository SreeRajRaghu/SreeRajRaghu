from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import requests
import vimeo


class VimeoConfig(models.Model):
    _name = 'vimeo.config'
    _description = 'Vimeo Configuration'
    _rec_name = 'company_id'

    access_token = fields.Char('Access Token')
    client_id = fields.Char('Client Id')
    user_id = fields.Char('User Id')
    client_secret = fields.Text('Client Secret')
    url = fields.Char('URL')
    school_code = fields.Char('Folder Id')
    folder_name = fields.Char('Folder Name')
    timeline = fields.Char('Timeline Id')
    e_learning = fields.Char('E-Learning Id')
    company_id = fields.Many2one('res.company', 'Institution', default=lambda self: self.env.user.company_id.id,
                                 required=True, index=1)

    @api.model
    def create(self, vals_list):   # create main folder in vimeo
        res = super(VimeoConfig, self).create(vals_list)
        user_id = self.test_connection(vals_list['access_token'])
        res.user_id = user_id
        url = "https://api.vimeo.com/me/projects"
        payload = 'name=%s' % vals_list['folder_name']
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer %s' % vals_list['access_token'],
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        folder_url = json.loads(response.text)
        folder_id = folder_url['uri'].split("/")[-1]
        res['school_code'] = folder_id
        return res

    @api.multi
    def unlink(self):
        url = "https://api.vimeo.com/me/projects/%s" % self.school_code
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.access_token,
        }
        requests.request("DELETE", url, headers=headers, data=payload)
        return super(VimeoConfig, self).unlink()

    @api.multi
    def test_connection(self, token):
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % token
        }
        response = requests.request("GET", 'https://api.vimeo.com/me', headers=headers)
        if response.status_code == 200:
            user_url = json.loads(response.text)
            user_id = user_url['uri'].split("/")[-1]
            return user_id
        else:
            print("Following error is produced")
            raise UserError(_("Invalid Connection %s!") % json.dumps(response.json(), indent=4))
            print('error')

    def create_sub_folders(self, source, folder_name):
        if not self[source]:
            url = "https://api.vimeo.com/me/projects"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer %s' % self.access_token,
            }
            response = requests.request("POST", url, headers=headers, data={
                'name': "%s" % folder_name if folder_name else source or 'Untitled',
                'parent_folder_uri': "/users/%s/projects/%s" % (self.user_id, self.school_code)
            })
            folder_url = json.loads(response.text)
            folder_id = folder_url['uri'].split("/")[-1]
            self.write({source: folder_id})
            return folder_id
        else:
            return self[source]

    def upload_video(self, source, video, filename, description=None, folder_name=None):
        folder_id = self.create_sub_folders(source, folder_name)
        if source and video and filename:
            client = vimeo.VimeoClient(key=self.client_id,
                                       secret=self.client_secret,
                                       token=self.access_token)
            url = client.upload(filename=video, data={
                'folder_uri': '/folders/%s' % self[source],
                'name': filename,
                'description': description,
            })
            return {"status": 'success', 'video_id': url, 'folder_id': folder_id}

    def delete_single_video(self, video_id):
        url = 'https://api.vimeo.com%s' % video_id
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % self.access_token
        }
        requests.delete(url, headers=headers)

    def delete_folder_video(self, source,  folder_id):
        url = "https://api.vimeo.com/users/%s/projects/%s?should_delete_clips=True" % (self.user_id, folder_id)

        payload = {}
        headers = {
            'Authorization': 'Bearer %s' % self.access_token
        }
        response = requests.request("DELETE", url, headers=headers, data=payload)
        print(response.text)
        if response:
            self[source] = None
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "connection success",
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise UserError('Error')

    def get_video(self, video_id):
        url = "https://api.vimeo.com%s" % video_id

        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.access_token,
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)
        return response.text

