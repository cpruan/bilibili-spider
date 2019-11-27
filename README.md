### 欢迎大家访问我的小站：[Pp's blog](https://cpruan.com/)

<br><br>

这里交个爬虫的作业（爬虫思路），要爬取的是Bilibili的用户数据。

起因是这样的，我也算是B站深度用户了，喜欢很多大up，于是想统计他们的粉丝数据，做个小小的数据分析。

粉丝数据自然就得自己爬了（难倒等小破站自己被人脱库吗？不不，我没有暗示什么）。

##### 爬虫的思路：

1. 先搞到up的粉丝id
2. 根据id查到粉丝的信息
3. 爬下来，存数据库，完事

但真实情况会麻烦一些。

经过几番观察（观察过程比较重要），我发现关于这些目标数据有几个特点：

1. B站不让看up的粉丝（访问限制，仅可查看前5页，共100个粉丝）
2. 我查到的B站用户数据共**8个**，**mid/昵称/性别/签名/等级/地区/注册时间/生日**，其他数据还可以有“是否大会员/粉丝的粉丝数/发布视频数/观看量”等，但我不感兴趣，同学们
3. 上述8个数据分为两部分：
	1. “mid/昵称/性别/签名/等级”，数据在多处出现，比较好爬
	2. “地区/注册时间/生日”，数据就只能在用户首页看到，现在貌似有的还隐藏了
4. 意味着要爬8个数据，需要发起2个GET请求，我表示没太必要（最终选择只爬前5个，减少服务器压力）

那么问题来了，从哪获取up的粉丝id？知道了粉丝id，去哪个url查个人信息？

我的折中方案是：选择从up的视频评论入手，我假定一般情况下**愿意在视频底下发评论的就是该up的粉丝**，所以爬评论区的用户就行，把他们当粉丝；
并且上述的“mid/昵称/性别/签名/等级”数据可以直接在评论区找到，也就是只需要爬2次：爬某up的视频id(mid)，评论区用户id(mid)。

## 写爬虫一定要考虑对别人服务器的影响！

第一步是看别人的robots协议，这个协议告知客户端，服务器上允许爬取的资源的位置。

> Robots协议（也称为爬虫协议、机器人协议等）的全称是“网络爬虫排除标准”（Robots ExclusionProtocol），网站通过Robots协议告诉搜索引擎哪些页面可以抓取，哪些页面不能抓取.

该协议一般位于网站主路径下，url格式为http(或https)://域名/robots.txt，如bilibili的robots协议位于https://www.bilibili.com/robots.txt 。

> User-agent: *
Disallow: /include/
Disallow: /mylist/
Disallow: /member/
Disallow: /images/
Disallow: /ass/
Disallow: /getapi
Disallow: /search
Disallow: /account
Disallow: /badlist.html
Disallow: /m/

这是bilibili的robots协议，不做详解了。

此外robots协议主要是服务商给机器型爬虫的“建议”，所谓“门防君子，不防小人”，robots协议并不能强制性禁止爬虫。

更多的还是靠大家自觉，我也呼吁大家遵守服务商的robots“建议”，并且控制并发量，不要给别人服务器造成太大压力（控制停顿时间**time.sleep()**，建议**qps>1s**）。

## 爬虫方案

### 伪造成浏览器，对用户url发起请求

...去年初学Python时爬过一次，方法简单粗暴，使用selenium/splinter库提供的无头浏览器功能，伪造成浏览器对服务器发起请求，这样不受AJAX的限制。

现在学了一点Django，明白AJAX本质上不过是换成JS向服务器发起请求而已，只要找到AJAX的request信息，就可能在Python中伪造一模一样的request请求。

无头浏览器的方法有明显优点，几乎可以完全模拟用户行为，返回的数据是渲染完毕的，也必然以明文呈现在HTML上（不然你让正常用户怎么浏览呢），因此AJAX的反爬方式就失效了。

缺点也很明显，浏览器的一次请求实际上背后是一大堆请求，其中的多数信息是你不需要的（如CSS、Font之类），这不仅浪费了你的硬件资源、爬取效率低，也对别人的服务器造成很大压力。

![image.png](https://i.loli.net/2019/11/27/eSZaCQUqnON9Y3c.png)

如上图，仅仅是访问bilibili主页，我们就发起了100+request，对服务器的消耗很大，也是浪费，不建议。

### 伪造成AJAX，对api url发起请求

这里需要一丢丢web开发知识，现在“前/后端分离”是主流，大部分数据并非是后端直接传给浏览器，而是先传给前端JS，再异步渲染到HTML页面上。

这种技术叫做AJAX，大家可以自己查阅资料。

前端AJAX的request/response毕竟是面对开发人员的，肯定比浏览器（面对用户）要来得简洁、高效一些，其专用的url也称为api，意指“与后端通讯的接口”（所以后端开发者也有被调侃为“写接口的”）。

所以一个好办法，是查找api，针对你想要的那部分数据发起请求就好。我们可以通过Chrome的调试工具，查找到目标数据是哪个api返回的。

比如我们来到这个B站影视区：https://www.bilibili.com/v/cinephile/

![image.png](https://i.loli.net/2019/11/27/W9JtXDya2zHK5kf.png)

比如想爬取“影视杂谈”板块中的12个视频的信息，我们打开chrome的“检查”功能，发现其数据是由这个request返回的。

##### request信息

**Request URL:**
https://api.bilibili.com/x/web-interface/dynamic/region

**params:**
	callback: jqueryCallback_bili_8319337549613472
	jsonp: jsonp
	ps: 15
	rid: 182
	_: 1574835755931

**request_headers:**
	Accept: */*
	Accept-Encoding: gzip, deflate, br
	Accept-Language: (此处省略)
	Connection: keep-alive
	Cookie: (此处省略)
	Host: api.bilibili.com
	Referer: https://www.bilibili.com/v/cinephile/
	Sec-Fetch-Mode: no-cors
	Sec-Fetch-Site: same-site
	User-Agent: (此处省略)

##### response信息

![image.png](https://i.loli.net/2019/11/27/cztG2QXZN4avbdW.png)

上述response返回的是jsonp格式，**JSONP**的部分我还没搞懂，有兴趣的同学可以看下这篇文章：

[浅谈浏览器端JavaScript跨域解决方法](http://blog.rccoder.net/javascript/2016/03/01/javascript-cross-domain.html "浅谈浏览器端JavaScript跨域解决方法")

或者这里

[浅谈浏览器端JavaScript跨域解决方法](https://github.com/rccoder/blog/issues/5 "浅谈浏览器端JavaScript跨域解决方法")

我就粗暴理解jsonp是在json外套了层壳，比如上面response的例子就是`jqueryCallback_bili_8319337549613472(json)`。

你会发现json外面套的壳子“jqueryCallback_bili_8319337549613472”，其实就是**params**中的**callback**的值。

### 发起request，解析response

完整代码我就不放了，主要描述下实现的方法。

发起请求用到requsts库，requests库大家可以查阅文档，还是很容易上手的：[快速上手 - Requests官方文档](https://cn.python-requests.org/zh_CN/latest/user/quickstart.html "快速上手 - Requests官方文档")

假定代码：

```
import requests

r = requests.get(url, params=params, headers=heasers)
if r.status_code == 200:
    text = r.text
```

我们要解析的数据就在`text`中，首先需要把jsonp转为json，列出两种方法。

其一就是字符串切片，利用`callback`参数的值：

```
import json

data = r.text[len(params['callback'])+1:-1]
json_data = json.loads(data)
```

其二，把**requests**中的**params**中的**callback**参数留空，或者把**jsonp**参数改为“json”，返回的response数据就直接是json而非jsonp了（不知道这个办法能用多久）。

json.loads()可以把str类型的json结构，转为Python中的dict类型。然后我们就很好取数据了。

观察json的结构：

![image.png](https://i.loli.net/2019/11/27/LtVkwOR8Az1q49j.png)

通过以下代码就可以打印**视频id**、**视频title**、**视频作者id**等等：

```
for video in json_data['data']['archives']:
    print(f"{video['aid']} {video['owner']['name']} - {video['title']}")
```

数据：

![image.png](https://i.loli.net/2019/11/27/5qILr8WuPUVH2XT.png)

基本原理就讲到这里啦，按原本的预期，下一步工作是找到**“up视频目录的api + 视频下评论目录的api”**，但我以前学习爬虫时已经做过一次，确实没有必要去对B站服务器发起不必要的request。

我觉得单纯讨论实现思路和相关技术，比获得数据更有趣（我好了你呢），因此就不提供完整代码了，拜拜。


