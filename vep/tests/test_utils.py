# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is PyVEP
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Ryan Kelly (rkelly@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import os
import unittest
import threading
import socket
import ssl
import json

from vep.errors import ConnectionError
from vep.utils import secure_urlopen, encode_bytes, decode_bytes
from vep.utils import encode_json_bytes, decode_json_bytes, get_assertion_info


def _filepath(name):
    return os.path.join(os.path.dirname(__file__), name)


class TestingServer(object):
    """Class to spin up a local SSL server with a self-signed certificate.

    This class runs a simple SSL server on localhost:8080, which will answer
    "OK" to any and all requests.  It uses a self-signed certificate from the
    file self.certfile.
    """

    def __init__(self):
        self.running = False
        self.certfile = _filepath("certs/selfsigned.crt")
        self.keyfile = _filepath("certs/selfsigned.key")

    def start(self):
        self.socket = socket.socket()
        self.socket.bind(("localhost", 8080))
        self.socket.listen(1)
        self.running = True
        self.runthread = threading.Thread(target=self.run)
        self.runthread.start()
        self.base_url = "https://localhost:8080"

    def run(self):
        while self.running:
            try:
                sock, addr = self.socket.accept()
                sock = ssl.wrap_socket(sock,
                                       server_side=True,
                                       certfile=self.certfile,
                                       keyfile=self.keyfile,
                                       ssl_version=ssl.PROTOCOL_SSLv3)
                try:
                    sock.sendall("HTTP/1.1 200 OK\r\n")
                    sock.sendall("Content-Type: text/plain\r\n")
                    sock.sendall("Content-Length: 2\r\n")
                    sock.sendall("\r\n")
                    sock.sendall("OK")
                finally:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
            except Exception:
                pass

    def shutdown(self):
        self.running = False
        try:
            secure_urlopen(self.base_url, timeout=1).read()
        except Exception:
            pass
        self.socket.close()
        self.runthread.join()
        del self.runthread
        del self.base_url


class TestUtils(unittest.TestCase):

    def test_secure_urlopen(self):
        server = TestingServer()
        server.start()
        try:
            kwds = {"timeout": 1}
            # We don't trust the server's certificate, so this fails.
            self.assertRaises(ConnectionError,
                              secure_urlopen, server.base_url, **kwds)
            # The certificate doesn't belong to localhost, so this fails.
            kwds["ca_certs"] = server.certfile
            self.assertRaises(ConnectionError,
                              secure_urlopen, server.base_url, **kwds)
            # Set a valid cert for local host, trust it, we succeed.
            server.certfile = _filepath("certs/localhost.crt")
            server.keyfile = _filepath("certs/localhost.key")
            kwds["ca_certs"] = server.certfile
            self.assertEquals(secure_urlopen(server.base_url, **kwds).read(),
                              "OK")
        finally:
            server.shutdown()

    def test_encode_decode_bytes(self):
        self.assertEquals("HELLO", decode_bytes(encode_bytes("HELLO")))
        self.assertEquals("HELLO", decode_bytes(encode_bytes(u"HELLO")))
        self.assertRaises(ValueError, decode_bytes, u"\N{SNOWMAN}")
        self.assertRaises(ValueError, decode_bytes, "A===")

    def test_encode_decode_json_bytes(self):
        obj = {"hello": "world"}
        self.assertEquals(obj, decode_json_bytes(encode_json_bytes(obj)))
        self.assertRaises(ValueError,
                          decode_json_bytes, encode_bytes("NOJSON4U"))
        self.assertRaises(ValueError,
                          decode_json_bytes, encode_bytes("42"))
        self.assertRaises(ValueError,
                          decode_json_bytes, encode_bytes("[1, 2, 3]"))
        self.assertRaises(ValueError, encode_json_bytes, 42)
        self.assertRaises(ValueError, encode_json_bytes, [1, 3, 3])

    def test_get_assertion_info(self):
        assertion = """
        eyJjZXJ0aWZpY2F0ZXMiOlsiZXlKaGJHY2lPaUpTVXpFeU9DSjkuZXlKcGMzTWlPaUppY
        205M2MyVnlhV1F1YjNKbklpd2laWGh3SWpveE16SXhPVFF4T1Rnek1EVXdMQ0p3ZFdKc2
        FXTXRhMlY1SWpwN0ltRnNaMjl5YVhSb2JTSTZJbEpUSWl3aWJpSTZJamd4TmpreE5UQTB
        OVGswTkRVek5EVTFPREF4TlRreU5Ea3hNemsyTkRFNE56RTJNVFUwTkRNNE5EWXdPREl6
        TXpBMU1USXlPRGN3TURRNE56TTFNREk1TURrek16a3lNRFkzTURFMU1qQTBORGd6TWpVM
        U56WXdOREE1TnpFeU9EYzNNVGswT1RVek1UQXdNVFEyTkRVek56TTJOakU0TlRVek5EY3
        hNakkxT0RreU16TTFPRFV4TWpZNU1EQXdOREF5TVRrMk9ERTBNRGtpTENKbElqb2lOalU
        xTXpjaWZTd2ljSEpwYm1OcGNHRnNJanA3SW1WdFlXbHNJam9pY25saGJrQnlabXN1YVdR
        dVlYVWlmWDAua19oaEtYMFRCVnUyX2szbV9uRDVOVWJfTktwX19PLTY1MW1CRUl3S1NZZ
        GlOenQwQm9WRkNEVEVueEhQTWJCVjJaejk0WDgtLVRjVXJidEV0MWV1S1dWdjMtNTFUOU
        xBZnV6SEhfekNCUXJVbmxkMVpXSmpBM185ZEhQeTMwZzRMSU9YZTJWWmd0T1Nva3MyZFE
        4ZDNvazlSUTJQME5ERzB1MDBnN3lGejE4Il0sImFzc2VydGlvbiI6ImV5SmhiR2NpT2lK
        U1V6WTBJbjAuZXlKbGVIQWlPakV6TWpFNU1qazBOelU0TWprc0ltRjFaQ0k2SW1oMGRIQ
        TZMeTl0ZVdaaGRtOXlhWFJsWW1WbGNpNXZjbWNpZlEuQWhnS2Q0eXM0S3FnSGJYcUNSS3
        hHdlluVmFJOUwtb2hYSHk0SVBVWDltXzI0TWdfYlU2aGRIMTNTNnFnQy1vSHBpS3BfTGl
        6cDRGRjlUclBjNjBTRXcifQ
        """.replace(" ", "").replace("\n", "").strip()
        data = get_assertion_info(assertion)
        self.assertEquals(data["principal"]["email"], "ryan@rfk.id.au")
        self.assertEquals(data["audience"], "http://myfavoritebeer.org")
        self.assertRaises(ValueError, get_assertion_info, "JUNK")
        self.assertRaises(ValueError, get_assertion_info, "X")
        self.assertRaises(ValueError, get_assertion_info, "\x00\x01\x02")
        bad_assertion = encode_json_bytes({"fake": "assertion"})
        self.assertRaises(ValueError, get_assertion_info, bad_assertion)
