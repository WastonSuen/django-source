
## Django项目启动步骤

### 1. 使用 python manage.py runserver 启动时
><1> 由环境变量 DJANGO_SETTINGS_MODULE 设置settings文件位置, 并且执行 execute_from_command_line(sys.argv)
```
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_source.settings")
```

><2> CommandParser 拼接启动参数(可从命令行更改 DJANGO_SETTINGS_MODULE, pythonpath)
> django.core.management.CommandParser
```
try:
    subcommand = self.argv[1]
except IndexError:
    subcommand = 'help'  # Display help if no arguments were given.
parser = CommandParser(None, usage="%(prog)s subcommand [options] [args]", add_help=False)
parser.add_argument('--settings')
parser.add_argument('--pythonpath')
parser.add_argument('args', nargs='*')  # catch-all
try:
    options, args = parser.parse_known_args(self.argv[2:])
    handle_default_options(options)
except CommandError:
    pass  # Ignore any option errors at this point.
```

><3> 调用setup, configure loggin 模块, load installed_app, 并进行 urls 自动补全
> django.core.management.ManagementUtility.execute
```
if settings.configured:
    if subcommand == 'runserver' and '--noreload' not in self.argv:
        try:
            autoreload.check_errors(django.setup)()
        except Exception:
            apps.all_models = defaultdict(OrderedDict)
            apps.app_configs = OrderedDict()
            apps.apps_ready = apps.models_ready = apps.ready = True
            _parser = self.fetch_command('runserver').create_parser('django', 'runserver')
            _options, _args = _parser.parse_known_args(self.argv[2:])
            for _arg in _args:
                self.argv.remove(_arg)
    else:
        django.setup()
```
> django.setup
```
configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
if set_prefix:
    set_script_prefix(
        '/' if settings.FORCE_SCRIPT_NAME is None else settings.FORCE_SCRIPT_NAME
    )
apps.populate(settings.INSTALLED_APPS)
```
><4> run_from_argv, excute

> django.core.management.base.BaseCommand
```
try:
    self.execute(*args, **cmd_options)
except Exception as e:
    if options.traceback or not isinstance(e, CommandError):
        raise
    # SystemCheckError takes care of its own formatting.
    if isinstance(e, SystemCheckError):
        self.stderr.write(str(e), lambda x: x)
    else:
        self.stderr.write('%s: %s' % (e.__class__.__name__, e))
    sys.exit(1)
finally:
    try:
        connections.close_all()
    except ImproperlyConfigured:
        # Ignore if connections aren't setup at this point (e.g. no
        # configured settings).
        pass
```
```
output = self.handle(*args, **options)
```
><5> 调用 handle, 启动服务器

> django.core.management.commands.runserver.inner_run
```
def run(self, **options):
    """Run the server, using the autoreloader if needed."""
    use_reloader = options['use_reloader']
    if use_reloader:
        autoreload.main(self.inner_run, None, options)
    else:
        self.inner_run(None, **options)
```
> django.core.servers.basehttp.run

> **可以看到默认使用WSGIServer启动服务器**
```
def run(addr, port, wsgi_handler, ipv6=False, threading=False, server_cls=WSGIServer):
    server_address = (addr, port)
    if threading:
        httpd_cls = type('WSGIServer', (socketserver.ThreadingMixIn, server_cls), {})
    else:
        httpd_cls = server_cls
    httpd = httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)
    if threading:
        # ThreadingMixIn.daemon_threads indicates how threads will behave on an
        # abrupt shutdown; like quitting the server by the user or restarting
        # by the auto-reloader. True means the server will not wait for thread
        # termination before it quits. This will make auto-reloader faster
        # and will prevent the need to kill the server manually if a thread
        # isn't terminating correctly.
        httpd.daemon_threads = True
    httpd.set_app(wsgi_handler)
    httpd.serve_forever()
```

><6> 最后调用 socketserver.serve_forever
```
def serve_forever(self, poll_interval=0.5):
    """Handle one request at a time until shutdown.
    Polls for shutdown every poll_interval seconds. Ignores
    self.timeout. If you need to do periodic tasks, do them in
    another thread.
    """
    self.__is_shut_down.clear()
    try:
        # XXX: Consider using another file descriptor or connecting to the
        # socket to wake this up instead of polling. Polling reduces our
        # responsiveness to a shutdown request and wastes cpu at all other
        # times.
        with _ServerSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            while not self.__shutdown_request:
                ready = selector.select(poll_interval)
                if ready:
                    self._handle_request_noblock()
                self.service_actions()
    finally:
        self.__shutdown_request = False
        self.__is_shut_down.set()
```

### 2.使用 uwsgi --ini uwsgi.ini 启动
> uwsgi.ini

```
[uwsgi]
socket = 127.0.0.1:10086
master = true
enable-threads = true
workers = 2

chdir = /home/www/django-source/
virtualenv = /home/www/django-source/env/
pp = /home/www/django-source/
module = django_source.wsgi
disable-logging = true
```
>**最终还是维护一个 WSGIHander**
```
def get_wsgi_application():
    """
    The public interface to Django's WSGI support. Return a WSGI callable.
    Avoids making django.core.handlers.WSGIHandler a public API, in case the
    internal WSGI implementation changes or moves in the future.
    """
    django.setup(set_prefix=False)
    return WSGIHandler()
```
