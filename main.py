import os
import json
import MySQLdb
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from flask import Flask, Response, request
load_dotenv(find_dotenv())
app = Flask(__name__)

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
c = conn.cursor(MySQLdb.cursors.DictCursor)

IMAGE_ENDPOINT = os.environ['IMAGE_ENDPOINT']
THUMBNAIL_ENDPOINT = os.environ['THUMBNAIL_ENDPOINT']

def Json(obj):
    def serialize(obj):
        # enable to serialize datetime object
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type '{type(obj).name}' is not JSON serializable")
    return Response(json.dumps(obj, default=serialize), mimetype='application/json')

def build_image_info(dic):
    if dic['image_info_id'] is None:
        return {
            'id': dic['id'],
            'filename': dic['filename'],
            'created_at': dic['created_at'],
            'urls': {
                'image_url': f"{IMAGE_ENDPOINT}/{dic['filename']}",
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
                'image_url': f"{IMAGE_ENDPOINT}/{dic['filename']}",
                'thumbnail_url': f"{THUMBNAIL_ENDPOINT}/{dic['filename']}",
                'source': dic['source'],
            },
        }

def build_range_query(max_id, since_id):
    if max_id is not None:
        if since_id is not None:
            return f'i.id BETWEEN {since_id} AND {max_id}'
        else:
            return f'i.id <= {max_id}'
    else:
        if since_id is not None:
            return f'i.id > {since_id}'
        else:
            return ''

@app.route('/sukui/api/image/<int:image_id>')
def get_image(image_id):
    image_id = int(image_id)
    query = '''
    SELECT
        i.id AS id
      , i.filename AS filename
      , i.created_at AS created_at
      , ii.id AS image_info_id
      , ii.comment AS comment
      , ii.source AS source
    FROM images i
    INNER JOIN image_info ii
    ON i.id = ii.image_id
    WHERE i.id = %s
    '''
    c.execute(query, (image_id,))
    result = c.fetchone()
    if result is None:
        return Json({'ok': False, 'message': 'image_not_found'})
    return Json({'ok': True, 'data': build_image_info(result)})

@app.route('/sukui/api/images')
def get_images():
    count = int(request.args.get('count', 20))
    max_id = request.args.get('max_id')
    since_id = request.args.get('since_id')
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
    INNER JOIN image_info ii
    ON i.id = ii.image_id
    {'WHERE ' + range_query if range_query else ''}
    ORDER BY id DESC LIMIT %s
    '''
    c.execute(query, (count,))
    result = c.fetchall()
    if result is None:
        return Json({'ok': False, 'message': 'invalid parameters'})
    return Json({'ok': True, 'data': [build_image_info(info) for info in result]})

@app.route('/sukui/api/images/search')
def search_images():
    count = int(request.args.get('count', 20))
    max_id = request.args.get('max_id')
    since_id = request.args.get('since_id')
    keyword  = f'%{request.args.get("keyword", "")}%'
    if keyword == '%%':
        return Json({'ok': False, 'message': 'you must specify a keyword'})

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
    INNER JOIN image_info ii
    ON i.id = ii.image_id
    WHERE
        ii.comment LIKE %s
    {'AND ' + range_query if range_query else ''}
    ORDER BY id DESC LIMIT %s
    '''
    c.execute(query, (keyword, count,))
    result = c.fetchall()
    if result is None:
        return Json({'ok': False, 'message': 'invalid parameters'})
    return Json({'ok': True, 'data': [build_image_info(info) for info in result]})

if __name__ == '__main__':
    app.run(host='0.0.0.0')
