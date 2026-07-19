#!/usr/bin/env python3
"""高一数学智能练习系统 - 本地静态文件服务器"""
import os, sys, socket

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'math_tutor.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print('高一数学智能练习系统')
    print('本地: http://localhost:%d' % port)
    try:
        ip = socket.gethostbyname(socket.gethostname())
        print('局域网: http://%s:%d' % (ip, port))
    except:
        pass
    app.run(host='0.0.0.0', port=port)
