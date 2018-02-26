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
