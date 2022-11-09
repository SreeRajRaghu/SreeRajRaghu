import logging

_logger = logging.getLogger(__name__)
_logger.info("================DROPBOX FIRST===================")
import dropbox
import io
import os
import base64

_logger.info("================DROPBOX SECOND===================")


def connect_dbx(ACCESS_TOKEN):
    try:
        dbx = dropbox.Dropbox(ACCESS_TOKEN)
        users_get_current_account = dbx.users_get_current_account()
        return dbx
    except:
        return False


def upload_a_file(dbx, raw_data, path, file_name):
    try:
        is_dir = os.path.basename(path) in [entry.name for entry in
                                            dbx.files_list_folder(os.path.dirname(path)).entries]
        if not is_dir:
            dbx.files_create_folder_v2(path)
        raw_data = base64.b64decode(raw_data)
        response = dbx.files_upload(raw_data, os.path.join(path, file_name))
        return {"status": "success",
                "response": response}

    except Exception as e:
        return {"status": "Error",
                "error": e}


def download_file(dbx, file_id):
    if file_id:
        try:
            response, content = dbx.files_download(file_id)
            link_response = dbx.files_get_temporary_link(file_id)
            file = io.BytesIO(content.content)
            data = file.read()
            raw_data = base64.encodestring(data)
            file_link = link_response.link
            return {"status": "success",
                    "raw_data": raw_data,
                    "file_link": file_link}
        except Exception as e:
            return {"status": "error",
                    "error": e}


def delete_file(dbx, file_id):
    try:
        dbx.files_delete_v2(file_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error",
                "error": e}

def is_dir_dbx(dbx, path):
    is_dir = os.path.basename(path) in [entry.name for entry in
                                        dbx.files_list_folder(os.path.dirname(path)).entries]
    if not is_dir:
        return False
    return True