# -*- coding:utf-8 -*-

from datetime import datetime
import logging
import pytz

_logger = logging.getLogger(__name__)

SISMATIX_DEFAULT_DATE_FORMAT = '%Y/%m/%d'
SISMATIX_DEFAULT_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'


def toUTC(d, tz):
    user_tz_str = tz
    if not user_tz_str:
        user_tz_str = "Asia/Kuwait"
    tz = pytz.timezone(user_tz_str)
    return tz.normalize(tz.localize(d)).astimezone(pytz.utc)


def validate_args(date_time, format, is_only_date):
    if not date_time:
        return False
    if not format and is_only_date:
        format = SISMATIX_DEFAULT_DATE_FORMAT
    elif not format:
        format = SISMATIX_DEFAULT_DATETIME_FORMAT
    else:
        format = format
    return format


def format_str_to_date(date_str, format, is_date=False):
    format = validate_args(date_str, format, is_date)
    if not format:
        return False
    try:
        if type(date_str) is not str:
            return False
        date_time = datetime.strptime(date_str, format)
        return date_time if not is_date else date_time.date()
    except Exception as e:
        print('Exception: >>>>>>>>>>>>>>>>>>>>>>>>>>>', e)
        _logger.debug('Error while converting datetime %s %s', date_str, format, exc_info=True)
        return False


def format_date_to_str(date_obj, format, is_date=False):
    format = validate_args(date_obj, format, is_date)
    if not format:
        return False
    try:
        print(type(date_obj))
        if type(date_obj) is not datetime or type(date_obj) is not datetime:
            return False
        date_time = date_obj.strftime(format)
        return date_time if not is_date else date_time.date()
    except Exception as e:
        print('Exception: >>>>>>>>>>>>>>>>>>>>>>>>>>>', e)
        _logger.debug('Error while converting datetime %s %s', date_obj, format, exc_info=True)
        return False


def date_change_tz(date_obj, tz):
    try:
        if type(date_obj) is not datetime or type(date_obj) is not datetime:
            return False
        return toUTC(date_obj, tz)
    except Exception as e:
        print('Exception: >>>>>>>>>>>>>>>>>>>>>>>>>>>', e)
        _logger.debug('Error while converting datetimezone %s %s', date_obj, tz, exc_info=True)
    return False


def str_date_change_tz(date_str, tz, format):
    try:
        date_obj = format_str_to_date(date_str, format)
        return date_change_tz(date_obj, tz)
    except Exception as e:
        print('Exception: >>>>>>>>>>>>>>>>>>>>>>>>>>>', e)
        _logger.debug('Error while converting datetimezone %s %s', date_str, tz, exc_info=True)
        return False


def _get_user_lang(record, lang_code):
    return record.env['res.lang']._lang_get(lang_code)


def _get_user_date_format(record, lang_code):
    lang = _get_user_lang(record, lang_code)
    return lang.date_format


def _get_user_time_format(record, lang_code):
    lang = _get_user_lang(record, lang_code)
    return lang.time_format


def _get_user_datetime_format(record, lang_code):
    lang = _get_user_lang(record, lang_code)
    return "%s %s" % (lang.date_format, lang.time_format)
