import os
import time
import json
import MySQLdb
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from flask import Flask, Response, request, g
load_dotenv(find_dotenv())
app = Flask(__name__)

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

def ngram(text):
    without_space = [x for x in text if x not in ' \t\r\n']
    return '+' +  ' +'.join([x + y for x, y in zip(without_space, without_space[1:])])

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

@app.route('/sukui/api/image/<int:image_id>')
def get_image(image_id):
    image_id = int(image_id)
    query = '''
    SELECT SQL_CACHE
        i.id AS id
      , i.filename AS filename
      , i.created_at AS created_at
      , ii.id AS image_info_id
      , ii.comment AS comment
      , ii.source AS source
    FROM images i
    LEFT JOIN image_info ii
    ON i.id = ii.image_id
    WHERE i.id = %s
    '''
    c = db()
    c.execute(query, (image_id,))
    result = c.fetchone()
    if result is None:
        return Json({'ok': False, 'message': 'image_not_found'}, 404)
    return Json({'ok': True, 'data': build_image_info(result)})

@app.route('/sukui/api/images')
def get_images():
    try:
        count = int(request.args.get('count', 20))
    except Exception:
        return Json({'ok': False, 'message': 'invalid count parameter'}, 400)

    if not 0 < count <= 200:
        return Json({'ok': False, 'message': 'count must be larger than 0 and smaller or equal than 200'}, 400)

    _reversed = request.args.get('reversed', '0') == '1'
    try:
        max_id = int(request.args.get('max_id'))
    except Exception:
        max_id = None
    try:
        since_id = int(request.args.get('since_id'))
    except Exception:
        since_id = None
    range_query = build_range_query(max_id, since_id)
    query = f'''
    SELECT SQL_CACHE
        i.id AS id
      , i.filename AS filename
      , i.created_at AS created_at
      , ii.id AS image_info_id
      , ii.comment AS comment
      , ii.source AS source
    FROM images i
    LEFT JOIN image_info ii
    ON i.id = ii.image_id
    {('WHERE ' + range_query) if range_query else ''}
    ORDER BY id {'ASC' if _reversed else 'DESC'} LIMIT %s
    '''
    t_s = time.time()
    c = db()
    c.execute(query, (count,))
    result = c.fetchall()
    if result is None:
        return Json({'ok': False, 'message': 'invalid parameters'}, 400)
    query = f'''
    SELECT SQL_CACHE
        COUNT(*) AS cnt
    FROM images
    '''
    c.execute(query)
    count = c.fetchone()['cnt']
    t_e = time.time()
    return Json({'ok': True, 'elapsed_time': t_e - t_s, 'whole_count': count, 'data': [build_image_info(info) for info in result]})

@app.route('/sukui/api/images/search')
def search_images():
    try:
        count = int(request.args.get('count', 20))
    except Exception:
        return Json({'ok': False, 'message': 'invalid count parameter'}, 400)

    if not 0 < count <= 200:
        return Json({'ok': False, 'message': 'count must be larger than 0 and smaller or equal than 200'}, 400)
    _reversed = request.args.get('reversed', '0') == '1'

    try:
        max_id = int(request.args.get('max_id'))
    except Exception:
        max_id = None
    try:
        since_id = int(request.args.get('since_id'))
    except Exception:
        since_id = None

    keyword  = request.args.get("keyword")
    if keyword is None:
        return Json({'ok': False, 'message': 'you must specify a keyword'}, 400)
    ngram_keyword = ngram(keyword)

    range_query = build_range_query(max_id, since_id)
    query = f'''
    SELECT
        i.id AS id
      , i.filename AS filename
      , i.created_at AS created_at
      , ii.id AS image_info_id
      , ii.comment AS comment
      , ii.source AS source
    FROM images i
    LEFT JOIN image_info ii
    ON i.id = ii.image_id
    WHERE
        MATCH (ii.comment_ngram) AGAINST (%s IN BOOLEAN MODE)
    AND ii.comment LIKE %s
    {('AND ' + range_query) if range_query else ''}
    ORDER BY id {'ASC' if _reversed else 'DESC'} LIMIT %s
    '''
    c = db()
    t_s = time.time()
    c.execute(query, (ngram_keyword, f'%{keyword}%', count,))
    result = c.fetchall()
    if result is None:
        return Json({'ok': False, 'message': 'invalid parameters'}, 400)
    query = f'''
    SELECT
        COUNT(*) AS cnt
    FROM images i
    LEFT JOIN image_info ii
    ON
        i.id = ii.image_id
    WHERE
        MATCH (ii.comment_ngram) AGAINST (%s IN BOOLEAN MODE)
    AND ii.comment LIKE %s
    '''
    c.execute(query, (ngram_keyword, f'%{keyword}%'))
    count = c.fetchone()['cnt']
    t_e = time.time()
    return Json({'ok': True, 'elapsed_time': t_e - t_s, 'whole_count': count, 'data': [build_image_info(info) for info in result]})

if __name__ == '__main__':
    app.run()
