try:
    import mysql.connector
except:
    pass

def get_connector():
    sql_connect = mysql.connector.connect(host='localhost', user='crawler', password=,
                                          database='ritsumeidb', charset='utf8')
    return sql_connect


def make_tables(conn, n):
    n = str(n)
    try:
        conn.ping(reconnect=True)
        cur = conn.cursor(dictionary=True)
        cur.execute("create table id_url_" + n + "(id int auto_increment, url varchar(256), index(id));")
        cur.execute("create table id_link_" + n + "(url_id int, link varchar(256));")
        cur.execute("create table id_redirect_" + n + "(url_id int, redirect varchar(256));")
        cur.execute("create table id_request_" + n + "(url_id int, request varchar(256));")
        cur.execute("create table id_ContentType_" + n + "(url_id int, ContentType varchar(64));")
        conn.commit()
    except:
        conn.rollback()
        return False
    else:
        return True


def execute_query(conn, query_list, value_list):
    try:
        conn.ping(reconnect=True)
        cur = conn.cursor(dictionary=True)
        for query, value in zip(query_list, value_list):
            cur.execute(query, value)
        conn.commit()
    except:
        conn.rollback()
        return False
    else:
        return True


def get_id_from_url(conn, url, n):
    n = str(n)
    try:
        conn.ping(reconnect=True)
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id FROM id_url_' + n + ' WHERE url = %s', [url])  # ' は \' にエスケープされる
        result = cur.fetchall()
        if result:
            id_ = result[0]['id']
        else:
            id_ = None
    except:
        return False
    else:
        return id_


def register_url(conn, url, n):
    n = str(n)
    # すでに登録されているかどうかチェックする
    result = get_id_from_url(conn, url, n)
    if result:
        return True

    # urlが登録されていなかった場合
    try:
        conn.ping(reconnect=True)
        cur = conn.cursor(dictionary=True)
        cur.execute('INSERT INTO id_url_' + n + ' (url) VALUES (%s)', [url])
        conn.commit()
    except:
        conn.rollback()
        return False
    else:
        return True
