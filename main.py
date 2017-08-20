import time
from flask import Flask, Response, request, g
from utils import *
app = Flask(__name__)

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
@set_params
def get_images(count, max_id, since_id):
    _reversed = request.args.get('reversed', '0') == '1'

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
@set_params
def search_images(count, max_id, since_id):
    _reversed = request.args.get('reversed', '0') == '1'

    keyword  = request.args.get("keyword")
    if keyword is None:
        return Json({'ok': False, 'message': 'you must specify a keyword'}, 400)
    ngram_keyword = ngram(keyword)

    range_query = build_range_query(max_id, since_id)
    keyword_query = build_keyword_query(keyword)

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
    c.execute(query)
    count = c.fetchone()['cnt']
    t_e = time.time()
    return Json({'ok': True, 'elapsed_time': t_e - t_s, 'whole_count': count, 'data': [build_image_info(info) for info in result]})

if __name__ == '__main__':
    app.run()
