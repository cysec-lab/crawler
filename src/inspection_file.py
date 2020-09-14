# そのうち消す？
def check_content_type(content_type):
    if content_type == 'application/x-shockwave-flash':
        return True
    elif content_type == 'application/octet-stream':
        return True
    elif content_type == 'application/x-msdownload':
        return True
    elif content_type == 'application/x-download':
        return True
    elif content_type == 'application/x-msdos-program':
        return True
    else:
        return False
