import json
import main
import os
import MySQLdb
from functools import wraps
from datetime import datetime
from flask import request, Response, g
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

IMAGE_ENDPOINT = os.environ['IMAGE_ENDPOINT']
THUMBNAIL_ENDPOINT = os.environ['THUMBNAIL_ENDPOINT']

def connect_db():
    if os.environ.get('DB_SOCKET'):
        conn = MySQLdb.connect(
            user=os.environ['DB_USER'],
            passwd=os.environ['DB_PASSWD'],
            unix_socket=os.environ['DB_SOCKET'],
            db=os.environ['DB_NAME'],
            use_unicode=True,
            charset='utf8mb4',
        )
    else:
        conn = MySQLdb.connect(
            user=os.environ['DB_USER'],
            passwd=os.environ['DB_PASSWD'],
            host=os.environ['DB_HOST'],
            db=os.environ['DB_NAME'],
            use_unicode=True,
            charset='utf8mb4',
        )
    return conn

def db():
    if not hasattr(g, 'db_conn'):
        g.db_conn = connect_db()
    return g.db_conn.cursor(MySQLdb.cursors.DictCursor)

def Json(obj, status_code=200):
    def serialize(obj):
        # enable to serialize datetime object
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type '{type(obj).name}' is not JSON serializable")
    return Response(json.dumps(obj, default=serialize), mimetype='application/json'), status_code

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

def ngram(text):
    if len(text) <= 1:
        return f'{text}*'
    else:
        without_space = [x for x in text if x not in ' \t\r\n']
        return '+' +  ' +'.join([x + y for x, y in zip(without_space, without_space[1:])])

# decorators

def set_count(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            count = int(request.args.get('count', 20))
        except Exception:
            return Json({'ok': False, 'message': 'invalid count parameter'}, 400)

        if not 0 < count <= 200:
            return Json({'ok': False, 'message': 'count must be larger than 0 and smaller or equal than 200'}, 400)

        return func(count, *args, **kwargs)
    return inner

def set_max_id(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            max_id = int(request.args.get('max_id'))
        except Exception:
            max_id = None

        return func(max_id, *args, **kwargs)
    return inner

def set_since_id(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            since_id = int(request.args.get('since_id'))
        except Exception:
            since_id = None

        return func(since_id, *args, **kwargs)
    return inner
