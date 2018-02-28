## '解释中间件处理流程',


> 从 WSGIHandler 分析，接收请求，封装 request, 调用 get_response，将 request 交给 middleware 处理

```
class WSGIHandler(base.BaseHandler):
    request_class = WSGIRequest

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_middleware()

    def __call__(self, environ, start_response):
        set_script_prefix(get_script_name(environ))
        signals.request_started.send(sender=self.__class__, environ=environ)
        request = self.request_class(environ)
        response = self.get_response(request)

        response._handler_class = self.__class__

        status = '%d %s' % (response.status_code, response.reason_phrase)
        response_headers = list(response.items())
        for c in response.cookies.values():
            response_headers.append(('Set-Cookie', c.output(header='')))
        start_response(status, response_headers)
        if getattr(response, 'file_to_stream', None) is not None and environ.get('wsgi.file_wrapper'):
            response = environ['wsgi.file_wrapper'](response.file_to_stream)
        return response
```

> 各中间件类的实现, self.get_response = get_response 这一句的作用为设置get_response为下一个middleware

```
class SessionMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

```

> SessionMiddleware 继承自 MiddlewareMixin, 其实现了```__call__```方法

```
def __call__(self, request):
    response = None
    if hasattr(self, 'process_request'):
        response = self.process_request(request)
    if not response:
        response = self.get_response(request)
    if hasattr(self, 'process_response'):
        response = self.process_response(request, response)
    return response
```

> 这里可以看到 process_request, get_response, process_response 流式执行, 但是并非如此，在 django.core.handlers.base.BaseHandler 类里有如下实现：

```
def get_response(self, request):
    """Return an HttpResponse object for the given HttpRequest."""
    # Setup default url resolver for this thread
    set_urlconf(settings.ROOT_URLCONF)

    response = self._middleware_chain(request)

    response._closable_objects.append(request)

    # If the exception handler returns a TemplateResponse that has not
    # been rendered, force it to be rendered.
    if not getattr(response, 'is_rendered', True) and callable(getattr(response, 'render', None)):
        response = response.render()

    if response.status_code == 404:
        logger.warning(
            'Not Found: %s', request.path,
            extra={'status_code': 404, 'request': request},
        )

    return response
```

> response 由 ```self._middleware_chain(request)``` 返回,

```
handler = convert_exception_to_response(self._get_response)
for middleware_path in reversed(settings.MIDDLEWARE):
    middleware = import_string(middleware_path)
    try:
        mw_instance = middleware(handler)
    except MiddlewareNotUsed as exc:
        if settings.DEBUG:
            if str(exc):
                logger.debug('MiddlewareNotUsed(%r): %s', middleware_path, exc)
            else:
                logger.debug('MiddlewareNotUsed: %r', middleware_path)
        continue

    if mw_instance is None:
        raise ImproperlyConfigured(
            'Middleware factory %s returned None.' % middleware_path
        )

    if hasattr(mw_instance, 'process_view'):
        self._view_middleware.insert(0, mw_instance.process_view)
    if hasattr(mw_instance, 'process_template_response'):
        self._template_response_middleware.append(mw_instance.process_template_response)
    if hasattr(mw_instance, 'process_exception'):
        self._exception_middleware.append(mw_instance.process_exception)

    handler = convert_exception_to_response(mw_instance)

# We only assign to this when initialization is complete as it is used as a flag
# for initialization being complete.
self._middleware_chain = handler
```


>1. 这一步的主要作用是， 反向遍历 settings.MIDDLEWARE, 设置前一个的get_response为后一个middleware, 即前面提到的 self.get_response = get_response，相当于实现了一个递归，不妨称之为中间件栈。再依次执行 process_request/get_response/process_response 方法, 如果返回HttpResponse，则直接返回process_response(request, response)的结果；如果上一个中间件没有定义 process_request 或者返回 None, 执行 get_response 方法, 即下一个中间件的 process_request，直到所有中间件处理完成，最后调用默认的 ```_get_response()``` 方法， 交给 view 函数处理，
>2. 同时，这一步还添加了```_view_middleware，_template_response_middleware，_exception_middleware```，第一个在 ```_get_response``` 方法调用 view 视图函数时作用， 后两者在调用 view 视图函数之后发挥作用。
>3. 当 view 视图函数返回后，依次处理 ```_view_middleware, (_template_response_middleware,) _exception_middleware```, 返回 HttpResponse 对象，
>4. 中间件栈开始出栈操作, 按 MIDDLEWARE 从下往上执行 process_response, 并将本 middleware 返回值交给上一个 middleware 处理，直到所有中间件处理完成
>5. 此时交由 WSGIHander 处理 HEADER, COOKIES 等，再调用 start_response 并 return response 完成响应
