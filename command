celery -A vocabulary worker -l info -P eventlet

# 脚本启动
cd /d C:\Users\Administrator\PycharmProjects\vocabulary
celery -A vocabulary worker -l info -P eventlet


# 生成as证书(windows)
软件下载目录：https://slproweb.com/products/Win32OpenSSL.html
set OPENSSL_CONF=C:\OpenSSL-Win64\bin\cnf\openssl.cnf
set RANDFILE=C:\Users\Administrator\.rnd
1. openssl.exe
2. genrsa -out c:\\root.key 1024
3. req -new -key c:\root.key -out c:\root.csr
error：Unable to load config info from /usr/local/ssl/openssl.cnf
检索GnuWin32 安装目录，找到openssl.cnf
req -new -newkey rsa:1024 -nodes -keyout c:\\root.key -config "C:\OpenSSL-Win64\bin\cnf\openssl.cnf" -out c:\\root.csr
4.生成自签名的证书
req -x509 -days 365 -key C:\root.key -in C:\root.csr -out C:\server.crt



# 安装库
pip install django-extensions
pip install django-werkzeug-debugger-runserver
pip install pyOpenSSL

配置setting.app
'werkzeug_debugger_runserver',
'django_extensions',

pip install django==2.0
pip install nltk
pip install django_celery_results
pip install django_tables2
pip install pdfminer3k
pip install Pillow
pip install celery
pip install eventlet
安装RabbitMQ，会提示安装Erlang
https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.7.8/rabbitmq-server-3.7.8.exe.asc
http://erlang.org/download/otp_win64_21.0.exe


先安装：mod_wsgi
下载：https://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi
pip install wheel
pip install xx.whl
获得配置信息
mod_wsgi-express.exe module-config


Define PYTHON_PATH "C:/Program Files/Python36"
Define PROJECT_PATH "D:/Users/PythonCharmProjects/vocabulary"

LoadFile "${PYTHON_PATH}/python36.dll"
LoadModule wsgi_module "${PYTHON_PATH}/lib/site-packages/mod_wsgi/server/mod_wsgi.cp36-win_amd64.pyd"
WSGIPythonHome "${PYTHON_PATH}"

#指定项目的wsgi.py配置文件路径,这个py文件是在你的Django项目中
WSGIScriptAlias / ${PROJECT_PATH}/vocabulary/wsgi.py

#指定项目目录,即你的Django项目路径
WSGIPythonPath  ${PROJECT_PATH}/

<Directory ${PROJECT_PATH}/vocabulary>
<Files wsgi.py>
    Require all granted
</Files>
</Directory>

#项目静态文件地址, Django项目中静态文件的路径
Alias /static ${PROJECT_PATH}/app/static
<Directory ${PROJECT_PATH}/app/static>
    AllowOverride None
    Options None
    Require all granted
</Directory>

#项目media地址, 上传图片等文件夹的路径
Alias /media ${PROJECT_PATH}/media
<Directory ${PROJECT_PATH}/media>
    AllowOverride None
    Options None
    Require all granted
</Directory>




