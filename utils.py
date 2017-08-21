import json
import os
import MySQLdb
from functools import wraps
from datetime import datetime
from flask import request, Response, g
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

IMAGE_ENDPOINT = os.environ['IMAGE_ENDPOINT']
THUMBNAIL_ENDPOINT = os.environ['THUMBNAIL_ENDPOINT']


def Json(obj, status_code=200):
    def serialize(obj):
        # enable to serialize datetime object
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(
            f"Object of type '{type(obj).name}' is not JSON serializable")
    return Response(
        json.dumps(obj, default=serialize),
        mimetype='application/json'
    ), status_code


def build_image_info(dic):
    if dic['image_info_id'] is None:
        return {
            'id': dic['id'],
            'filename': dic['filename'],
            'created_at': dic['created_at'],
            'urls': {
                'original_url': f"{IMAGE_ENDPOINT}/{dic['filename']}",
                'thumbnail_url': f"{THUMBNAIL_ENDPOINT}/{dic['filename']}",
            },
        }
    else:
        return {
            'id': dic['id'],
            'filename': dic['filename'],
            'created_at': dic['created_at'],
            'comment': dic['comment'],
            'urls': {
                'original_url': f"{IMAGE_ENDPOINT}/{dic['filename']}",
                'thumbnail_url': f"{THUMBNAIL_ENDPOINT}/{dic['filename']}",
                'source': dic['source'],
            },
        }


def build_range_query(max_id, since_id):
    if max_id is None:
        if since_id is None:
            return ''
        else:
            return f'i.id > {since_id}'
    else:
        if since_id is None:
            return f'i.id <= {max_id}'
        else:
            return f'i.id > {since_id} AND i.id <= {max_id}'


def build_keyword_query(keyword):
    ret = []
    keywords = keyword.split()
    next_or = False

    for kw in keywords:
        if kw.startswith('-'):
            kw = kw[1:]
            ret.append(f'''
            ii.comment NOT LIKE
            '%%{MySQLdb.escape_string(kw).decode('utf-8')}%%'
            ''')
        elif kw == 'OR':
            next_or = True
        else:
            query = ''
            if next_or:
                query += ' OR ('

            if '+' in kw or '-' in kw or '(' in kw or ')' in kw:
                query += f'''
                MATCH (ii.comment_ngram) AGAINST
                ('{MySQLdb.escape_string(kw).decode('utf-8')}'
                IN NATURAL LANGUAGE MODE)
                AND ii.comment LIKE
                '%%{MySQLdb.escape_string(kw).decode('utf-8')}%%'
                '''
            else:
                query += f'''
                MATCH (ii.comment_ngram) AGAINST
                ('{MySQLdb.escape_string(ngram(kw)).decode('utf-8')}'
                IN BOOLEAN MODE)
                AND ii.comment LIKE
                '%%{MySQLdb.escape_string(kw).decode('utf-8')}%%'
                '''
            if next_or:
                query += ') '
                next_or = False
                if len(ret) > 0:
                    ret[-1] += query
                else:
                    ret.append(query.replace(' OR (', '('))
            else:
                ret.append(query)
    return 'AND '.join(ret)


def ngram(text):
    if len(text) <= 1:
        return f'{text}*'
    else:
        without_space = [x for x in text if x not in ' \t\r\n']
        return '+' + ' +'.join([
            x + y for x, y in zip(without_space, without_space[1:])
        ])

# decorators


def set_params(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            count = int(request.args.get('count', 20))
        except Exception:
            return Json({
                'ok': False,
                'message': 'invalid count parameter'
            }, 400)

        if not 0 < count <= 200:
            return Json({
                'ok': False,
                'message': 'count must be between 1 and 200'
            }, 400)

        try:
            max_id = int(request.args.get('max_id'))
        except Exception:
            max_id = None

        try:
            since_id = int(request.args.get('since_id'))
        except Exception:
            since_id = None

        return func(count, max_id, since_id, *args, **kwargs)
    return inner
