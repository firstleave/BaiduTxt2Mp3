# coding=utf-8
import json
import random
import sys, requests
from functools import partial
from urllib.error import URLError
from urllib.parse import urlencode, quote_plus
from urllib.request import Request, urlopen

from PyQt5.QtGui import QMouseEvent
from mainform import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import *


class MainWindow(QMainWindow):
    _startPos = None
    _endPos = None
    _isTracking = False

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mouseMoveEvent(self, e: QMouseEvent):
        self._endPos = e.pos() - self._startPos
        self.move(self.pos() + self._endPos)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.x(), e.y())

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None


class Baidu(QMainWindow):
    TTS_URL = 'http://tsn.baidu.com/text2audio'

    def fetchToken(self, window, tokenpath):
        host = 'http://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + window.api + '&client_secret=' + window.secret
        response = requests.get(host)
        if response:
            result = response.json()
            if 'access_token' in result.keys() and 'scope' in result.keys():
                if not 'audio_tts_post' in result['scope'].split(' '):
                    window.showInfomation('请检查是否拥有语音合成权限')
                    return ""
                with open(tokenpath, 'w') as of:
                    of.write(result['access_token'])
                    return result['access_token']

    def readToken(self, window):
        tokenpath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'token.txt')

        if not os.path.exists(tokenpath):
            return self.fetchToken(window, tokenpath)
        else:
            with open(tokenpath, 'r') as of:
                return of.read()

    def mixvoice(self, window):
        perlist = [0, 1, 3, 4, 0, 5118, 106, 110, 111, 103, 5, 5003]
        tok = self.readToken(window)
        if tok == "" or tok is None:
            return
        txt = window.textEdit.toPlainText()
        spd = window.spd.value()
        pit = window.pit.value()
        vol = window.vol.value()
        per = perlist[window.per.currentIndex()]
        text = quote_plus(txt)
        params = {'tok': tok, 'tex': text, 'cuid': 'BLOODO', 'lan': 'zh', 'ctp': 1, 'spd': spd, 'pit': pit, 'vol': vol,
                  'per': per}
        data = urlencode(params)
        req = Request(self.TTS_URL, data.encode('utf-8'))
        has_error = False
        try:
            f = urlopen(req)
            result_str = f.read()
            headers = dict((name.lower(), value) for name, value in f.headers.items())
            has_error = ('content-type' not in headers.keys() or headers['content-type'].find('audio/') < 0)
            if has_error:
                js=json.loads(result_str)
                if js["err_no"]=="502":
                    tokenpath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'token.txt')
                    self.fetchToken(window,tokenpath)
                    self.mixvoice(window)
                else:
                    window.showInfomation("错误:"+js["err_no"]+" "+js["err_msg"])
                    return
        except  URLError as err:
            print('http response http code : ' + str(err.code))
            result_str = err.read()
            has_error = True

        save_file = "error.txt" if has_error else u'合成_'+ str(random.randint(0,9999999))+'.mp3'
        with open(save_file, 'wb') as of:
            of.write(result_str)
        window.showInfomation("文件保存成功: " + save_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    myWin = Ui_MainWindow()
    myWin.setupUi(win)
    bd = Baidu(win)
    myWin.pushButton.clicked.connect(win.showMinimized)
    myWin.pushButton_2.clicked.connect(app.exit)
    convertClicked = partial(bd.mixvoice, myWin)
    myWin.convertbtn.clicked.connect(convertClicked)
    win.show()
    sys.exit(app.exec())
