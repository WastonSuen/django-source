## 'django.middleware',
**Django 中间件**

>请求流程:

>1. 接收用户请求, request
>2. 请求到达request middlewares, 中间件对request做一些预处理或者直接response请求
>3. URLConf通过urls.py文件和请求的URL找到相应的View
>4. View Middlewares被访问，它同样可以对request做一些处理或者直接返回response
>5. 调用views中的业务处理函数
>6. Views 可以返回一个特殊的context(Template用其生成页面并渲染输出), 或者直接返回Response Class
>7. HTTPResponse被发送到Response Middlewares
>8. 任何Response Middlewares都可以修改或丰富response
>9. Response返回到浏览器，呈现给用户


>tips:
>1. 加载middleware时严格按照MIDDLEWARE列表的顺序，request 时顺序，response时逆序

```
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```
>2. request 时加载 process_request 方法, 可以修改全局 request, response 时加载 process_response 方法, 可以修改全局 response

```
class SessionMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

    def process_request(self, request):
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            pass
        ......
```
