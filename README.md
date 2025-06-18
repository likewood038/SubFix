# 原项目地址
[SubFix](https://github.com/cronrpc/SubFix)

# Change Log
V2:汉化，添加裁剪音频功能，删除音频时同时删除音频文件

V3:为裁剪音频添加先自动提交文本，再执行裁剪的功能

# 安装

```
conda create -n audio_label python=3.10
conda activate audio_label
cd audio_label
pip install -r requirements.txt
```



# 使用

## 启动

```
python subfix_webui_V3.py [可选参数]
```

默认使用`./data/test.list`文件启动服务

### 可选参数

`--load_list [.list文件路径]` 指定.list文件路径

`--is_share True` 是否生成Gradio公网分享地址

`--webui_port 9875` 指定服务端口，默认8080

`--g_batch [10]`  指定一批次音频数量，默认为10



## 功能说明

提交文本:将窗口内的文本存入内存并写入文件

跳转索引:跳转至指定音频位置的页面

分割音频:将选定的音频,在指定的秒数位置截断为两个音频文件

裁剪音频:从选定的音频中,裁剪出A%到B%位置的音频,并删除其余内容(不可恢复)

删除音频:删除所选条目及音频文件(不可恢复)

合并音频:合并所选音频文件

下批索引:跳转至下一页

上批索引:跳转至上一页

提交并下批索引:提交文本+下批索引

反选:反选所选项

保存文件:将内存中的数据写入文件(基本无用)







