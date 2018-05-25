# 问题描述

这几天远哥一直嫌弃我pdf导出功能不行，和其他专业的网站没法比，哈哈，然后我就开始尝试着升级我的pdf导出工具。

# 依赖环境

- texlive 2017 (请用iso镜像安装而不要使用yum或者apt，我就丢失了tlmgr这个重要命令)

- pandoc 2.x （2.x版本支持md中使用https协议的图片, 不过使用参数和1.x有所不同）

# 下载模板

> 好的开始是成功的一半，好的模板可以让我们的pdf拥有更好的样式。

我使用的是[github的一个开源模板](https://github.com/Wandmalfarbe/pandoc-latex-template)。

这个模板风格很好, 关键是支持代码块和语法高亮。

![](https://github.com/Wandmalfarbe/pandoc-latex-template/raw/master/examples/custom-titlepage/custom-titlepage.png)

![](https://github.com/Wandmalfarbe/pandoc-latex-template/raw/master/examples/basic-example/basic-example.png)

由于我们只需要 eisvogel.tex 文件，所以创建目录:

	mkdir -p ~/.pandoc/templates/

把 eisvogel.tex 文件修改成 eisvogel.latex 放入到 ~/.pandoc/templates/ 中，修改的目的是在使用的时候不用添加文件后缀，可以直接用 

	--template eisvogel 

否则要用全名，不然提示找不到文件。

# 操作步骤

由于linux 不存在很多好看的字体，所以需要我们手动安装。

首先把ttf字体文件放入到 /usr/share/fonts/下的某一个文件夹，也可以自己创建一个新的子目录。

运行一下命令加载字体:

```shell
mkfontscale
mkfontdir
fc-cache -fv
fc-list | grep xxx 		# xxx 为安装的字体名
```

由于这个模板不支持中文和xelatex编译器，所以我们只能指定字体，我指定的字体为宋体(SimSun)。

> 这个模板的语法类似于脚本语言, 可以接受命令行参数，如果该参数没有被指定则使用默认参数， 一个 -V 只能指定一个参数，如果需要多个参数则需要多个 -V, 下面的命令我们指定CJKmainfont(全文默认字体)为宋体。

命令如下:

```shell
pandoc test.md --template eisvogel --pdf-engine xelatex -o e.pdf -V CJKmainfont='SimSun' -N --highlight-style pygments --listings
```

如果不出意外，就会生成一个名字叫做 e.pdf的文档。

> 详细的模板参数文档可以查看eisvogel模板的文档。

# 表格转换异常

以上步骤在使用过程中基本上都能正常使用，唯一有问题的就是表格。转换时不允许表格中有 html 转义字符， 如 <, > 等，如果出现那么这个表格将会转换失败。我们也不能全局替换，因为我们在使用 “引用”和“代码块”语法时依赖于 < 和 > 符号，所以我们要分析出表格中含有的转义字符，将其转换并且忽略其他地方的转义字符。

以下是我的算法大致步骤:

```Python
	import cgi # 这个模块可以方便的对html字符串进行转义和反转义
    import re
    _file = open("out.md", "wb")  # 输出文件
	info = open("read.md", "r").read()  # 输入文件
    line_list = info.split("\n")
    pattren = re.compile(r"\|.+\|")
    begin = re.compile(r"\|[-]+\|")

    tmp = ""
    status = False

    for line in line_list:
        if begin.match("".join(line.split())) and tmp:
            status = True
        elif pattren.match(line.strip()) and not status:
            if tmp:
                _file.write(tmp + "\n")
            tmp = line
            continue
        elif status and not pattren.match(line.strip()):
            status = False
        if status:
            if tmp:
                _file.write(cgi.escape(tmp) + "\n")
            _file.write(cgi.escape(line) + "\n")
        else:
            if tmp:
                _file.write(tmp + "\n")
            _file.write(line + "\n")
        tmp = ""

    if tmp:
        _file.write(tmp + "\n")
    _file.close()
```

```latex
f(x) = \int_{-\infty}^\infty
    \hat f(\xi)\,e^{2 \pi i \xi x}
    \,d\xi
```

通过以上的函数可以将一个md文件转换成我们需要的md文件，接下来就可以进行pdf的转换操作。














