import os
import re
import MySQLdb
from unicodedata import normalize
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


def connect_db():
    if os.environ.get('DB_SOCKET'):
        conn = MySQLdb.connect(
            user=os.environ['DB_USER'],
            passwd=os.environ['DB_PASSWD'],
            unix_socket=os.environ['DB_SOCKET'],
            db='sukui',
            use_unicode=True,
            charset='utf8mb4',
        )
    else:
        conn = MySQLdb.connect(
            user=os.environ['DB_USER'],
            passwd=os.environ['DB_PASSWD'],
            host=os.environ['DB_HOST'],
            db='sukui',
            use_unicode=True,
            charset='utf8mb4',
        )
    return conn


def db():
    db_conn = connect_db()
    return db_conn.cursor(MySQLdb.cursors.DictCursor)


def ngram(text):
    # Remove URL
    text = re.sub(r'https?://[a-zA-Z0-9\./]+', '', text)

    without_space = [x for x in text if x not in ' \t\r\n']
    return ' '.join([x + y for x, y in zip(without_space, without_space[1:])])


def main():
    c = db()
    c.execute('BEGIN')
    try:
        c.execute('SELECT id, comment FROM image_info '
                  'WHERE comment IS NOT NULL')
        for row in c.fetchall():
            # comment_norm = normalize('NFKD', row['comment'])
            comment_norm = row['comment']
            c.execute('UPDATE image_info SET '
                      'comment = %s, comment_ngram = %s '
                      f'WHERE id = {row["id"]}',
                      (comment_norm, ngram(comment_norm),))
    except Exception:
        print('ROLLBACK')
        c.execute('ROLLBACK')
        raise
    else:
        print('COMMIT')
        c.execute('COMMIT')


if __name__ == '__main__':
    main()
