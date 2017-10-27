"""Server function."""
import email.utils
import sys
import os
from gevent.server import StreamServer


def response_error(error_code):
    """Determine and format proper response."""
    if error_code == '405':
        error_msg = 'METHOD NOT ALLOWED'
    elif error_code == '505':
        error_msg = 'HTTP VERSION NOT SUPPORTED'
    elif error_code == '500':
        error_msg = 'INTERNAL SERVER ERROR'
    elif error_code == '404':
        error_msg = 'CONTENT NOT FOUND'
    send_error_response = """
    HTTP/1.1 {}\r\n
     DATE: {}\r\n
     ERROR: {}\r\n
    """.format(error_code, email.utils.formatdate(usegmt=True), error_msg)

    message = u'{}*'.format(send_error_response)
    return message


def parse_request(msg):
    """Parse the incoming msg to check for proper format, raise appropriate exception."""
    request = msg.split(' ')

    if request[0] == 'CRASH':
        raise ValueError('500')
    elif request[0] == 'GET' and request[2] == 'HTTP/1.1':
        uri = request[1]
        try:
            message_return = resolve_uri(uri)
        except IndexError:
            raise ValueError('404')
        return [message_return, request]
    elif request[0] != 'GET':
        raise ValueError('405')
    elif request[2] != 'HTTP/1.1':
        raise ValueError('505')


def resolve_uri(uri):
    """."""
    os.chdir('..')
    os.chdir('web_home_directory')
    if uri.endswith('/'):
        if not os.path.isdir(uri):
            raise IndexError
        else:
            html_list = [s for s in os.listdir(uri) if s.endswith('.jpg')]
            html_count = len(html_list)
            result = response_ok((html_list, html_count, 'HTML LISTING'))
            return result
    else:
        if not os.path.exists(uri):
            raise IndexError
        else:
            extension = os.path.splitext(uri)[1]
            txt = ''
            with open(uri, 'r') as f:
                txt = f.read()
            txt_len = len(txt)
            result = response_ok((txt, txt_len, extension))
            return result


def handle_conn(conn, addr):
    """Handle incoming request."""
    buffer_len = 8
    msg = ''
    while True:
        data = (conn.recv(buffer_len)).decode('utf8')
        msg += data

        if data.endswith('*'):
            try:
                message_return = parse_request(msg)[0]
            except ValueError as err:
                message_return = response_error(err.args[0])
            conn.send(message_return.encode('utf8'))
            logged_request = """
            INCOMING REQUEST\r\n
            REQUEST BODY: {}\r\n
            FROM: {}\r\n
            DATE: {}\r\n
            """.format(
                msg,
                addr,
                email.utils.formatdate(usegmt=True))
            sys.stdout.write(logged_request)
            msg = ''
            break


def server():
    """Create the stream server."""
    try:
        stream = StreamServer(('127.0.0.1', 3000), handle_conn)
        stream.serve_forever()
    except KeyboardInterrupt:
        pass


def response_ok(msg):
    """Send the 200 ok msg if called."""
    send_ok_response = """
HTTP/1.1 200 OK \r\n
FILE TYPE: {type}
FILE LENGTH:{len}
DATE: {date} \r\n
\r\n
BODY: \r\n {body}
\r\n
    """.format(date=email.utils.formatdate(usegmt=True), type=msg[2], len=msg[1], body=msg[0])
    message = u'{}*'.format(send_ok_response)
    return message


if __name__ == '__main__':
    try:
        server()
    except KeyboardInterrupt:
        pass
