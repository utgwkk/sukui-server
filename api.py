import time
import os
import MySQLdb
from flask import Flask, request, g, Response
from utils import (
    Json, build_image_info, build_range_query, build_keyword_query,
    build_search_query_from_dic, set_params
)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
app = Flask(__name__)


def connect_db():
    kwargs = dict(
        user=os.environ['DB_USER'],
        passwd=os.environ['DB_PASSWD'],
        host=os.environ['DB_HOST'],
        port=int(os.environ['DB_PORT']),
        db=os.environ['DB_NAME'],
        use_unicode=True,
        charset='utf8mb4',
    )

    if app.testing:
        kwargs['db'] = os.environ['TEST_DB_NAME']

    return MySQLdb.connect(**kwargs)


def db():
    if not hasattr(g, 'db_conn'):
        g.db_conn = connect_db()
    return g.db_conn.cursor(MySQLdb.cursors.DictCursor)


@app.route('/ping')
def ping():
    return Response('pong', mimetype='text/plain')


@app.route('/image/<int:image_id>')
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
    LEFT JOIN image_info ii
    ON i.id = ii.image_id
    WHERE i.id = %s
    '''
    app.logger.debug(f'Query: {query}' % image_id)
    c = db()
    c.execute(query, (image_id,))
    result = c.fetchone()
    if result is None:
        return Json({'ok': False, 'message': 'image_not_found'}, 404)
    return Json({'ok': True, 'data': build_image_info(result)})


@app.route('/images')
@set_params
def get_images(count, max_id, since_id):
    _reversed = request.args.get('reversed', '0') == '1'

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
    {('WHERE ' + range_query) if range_query else ''}
    ORDER BY id {'ASC' if _reversed else 'DESC'} LIMIT %s
    '''
    app.logger.debug(f'Query: {query}' % count)
    t_s = time.time()
    c = db()
    c.execute(query, (count,))
    result = c.fetchall()
    if result is None:
        return Json({'ok': False, 'message': 'invalid parameters'}, 400)
    query = f'''
    SELECT
        COUNT(*) AS cnt
    FROM images
    '''
    app.logger.debug(f'Query: {query}')
    c.execute(query)
    count = c.fetchone()['cnt']
    t_e = time.time()
    return Json({
        'ok': True,
        'elapsed_time': t_e - t_s,
        'whole_count': count,
        'data': [build_image_info(info) for info in result]
    })


@app.route('/images/search')
@set_params
def search_images(count, max_id, since_id):
    _reversed = request.args.get('reversed', '0') == '1'

    keyword = request.args.get("keyword", "").strip()
    and_keyword = request.args.get("all", "").strip()
    or_keyword = request.args.get("any", "").strip()
    not_keyword = request.args.get("ex", "").strip()
    if keyword:
        keyword_query = build_keyword_query(keyword)
    elif and_keyword or or_keyword or not_keyword:
        query_dic = {
            "and": and_keyword.split(),
            "or": or_keyword.split(),
            "ex": not_keyword.split(),
        }
        keyword_query = build_search_query_from_dic(query_dic)
    else:
        return Json({
            'ok': False,
            'message': 'you must specify a keyword'
        }, 400)

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
        {keyword_query}
    {('AND ' + range_query) if range_query else ''}
    ORDER BY id {'ASC' if _reversed else 'DESC'} LIMIT %s
    '''
    app.logger.debug(f'Query: {query}')
    c = db()
    t_s = time.time()
    c.execute(query, (count,))
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
        {keyword_query}
    '''
    app.logger.debug(f'Query: {query}')
    c.execute(query)
    count = c.fetchone()['cnt']
    t_e = time.time()
    return Json({
        'ok': True,
        'elapsed_time': t_e - t_s,
        'whole_count': count,
        'data': [build_image_info(info) for info in result]
    })


if __name__ == '__main__':
    app.run()
