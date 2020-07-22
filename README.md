# 中国土地市场网lanchina.com数据采集爬虫 Python+SVM破解验证码、突破翻页限制



# 自动爬取过程分析

最近看到有人需要爬取中国土地市场网lanchina.com的土地交易数据，一时手痒。花了小半天对这个网站进行了一些分析，利用scrapy框架开发了一个简单的爬虫程序。主要实现了验证码识别、请求参数解析、自动翻页等小功能。第一次在CSDN上写博客，写的不好，请多谅解！

> 联系方式：
> QQ：345563121
> 邮箱：modianserver@gmail.com

## 验证码反爬与破解

当我们第一次访问**https://www.landchina.com/default.aspx?tab=263**时，会弹出验证码界面，需要输入正确的验证码才能正常访问官网：![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722163117219.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70 )
1. **验证码如何破解：**

> - 调用在线验证码识别接口（百度API）
> - 本地构建数据集与模型进行训练识别

我对第三方的在线识别服务不是很了解，所以还是选择了自己在本地采集少量数据样本，利用SVM模型进行分类训练。讲下为什么我会选择自己采集数据与训练模型：

> - 验证码排列规则，分割极其容易！
> - 验证码清晰，识别难度相当低！


**采集到验证码：**
![完整的验证码](https://img-blog.csdnimg.cn/20200722165637780.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)
**分割后的单个字符：**
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722165800728.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)
**人工挑选出两组[0-9]的样本图像：**
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722165844641.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)

> **至此，数据集已经准备好了，接下来利用sklearn库构建SVM模型对数据集进行训练与分类，得到一个效果不错的模型。效果如下图：**

![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722170740674.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)
## 访问跳转、字段加密
当输入正确的验证码后，点击`继续访问网站`后如何跳转呢？经过抓包分析，
网站的JS代码将`5位验证码`转成`16进制数字`，具体功能函数如下图：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722172555819.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)

## 自动翻页JS代码分析与破解
官网在`结果公示`页面最多可查询`200页`的数据记录，但是绝大多数情况下按照我们的搜索规则会搜索到超过`200页`的记录，那么有没有什么办法可以突破访问呢？
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722173214136.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)
通过分析查询对应的JS代码，我们仿佛看了希望，直接上图：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722173414123.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)
`GoPage（t,n）`是页面的翻页函数，翻页限制仅仅是在前端JS代码中做了变量检查，`o && o.submit()`则是调用了Form表单的提交功能，那么我只需要观察这个请求到底发送了哪些信息，然后如法炮制模拟发送，就能达到我想要的翻页效果。这是翻页请求携带的Cookie信息：![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722173908735.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)
**红色框框中的字段就是代表页数，经过测试可以突破翻页限制！**

## 爬取过程中的调整技巧
1. 在采集验证码的过程中，请求速度不能太快，否则网站直接封IP，时间大概是一天！
2. 爬虫采集数据过程中不能并发，否则IP会被拉黑，但是这个拉黑时间可能只有10分钟！
3. 如果爬取的数据量过大，可以分时间段爬取，按月搜索采集。


**经过测试，1000条数据需要花费8分钟时间抓取解析，最后放一张效果图：**
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200722174757998.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2ExMTM4NzE2NDYzMw==,size_16,color_FFFFFF,t_70)


