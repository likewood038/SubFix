import argparse
import os
import copy
import json
import uuid

try:
    import gradio.analytics as analytics

    analytics.version_check = lambda: None
except:
    ...

import librosa
import gradio as gr
import numpy as np
import soundfile

g_json_key_text = ""
g_json_key_path = ""
g_load_file = ""
g_load_format = ""

g_max_json_index = 0
g_index = 0#当前batch的头索引
g_batch = 10#batch大小
g_text_list = []
g_audio_list = []
g_checkbox_list = []
g_data_json = []#全部数据[{'wav_path': 'data/test/9.11.wav', 'speaker_name': 'test', 'language': 'ZH', 'text': '谢谢这个啊， 乐。 谢谢你。'},,,,]
g_audio_cut_checkbox_list=[]


def reload_data(index, batch):
    global g_index
    g_index = index
    global g_batch
    g_batch = batch
    datas = g_data_json[index : index + batch]#从全部数据中取出特定1batch
    output = []
    for d in datas:
        output.append({g_json_key_text: d[g_json_key_text], g_json_key_path: d[g_json_key_path]})
    return output


def b_change_index(index, batch):
    '''
        从g_data_json获取用于更新页面文字,语音,勾选状态的字典数组
    '''
    global g_index, g_batch
    g_index, g_batch = index, batch
    datas = reload_data(index, batch)
    output = []
    for i, _ in enumerate(datas):
        output.append(
            # gr.Textbox(
            #     label=f"Text {i+index}",
            #     value=_[g_json_key_text]#text
            # )
            {"__type__": "update", "label": f"Text {i + index}", "value": _[g_json_key_text]}
        )
    for _ in range(g_batch - len(datas)):
        output.append(
            # gr.Textbox(
            #     label=f"Text",
            #     value=""
            # )
            {"__type__": "update", "label": "Text", "value": ""}
        )
    for _ in datas:
        output.append(_[g_json_key_path])
    for _ in range(g_batch - len(datas)):
        output.append(None)
    for _ in range(g_batch):
        output.append(False)

    '''
        print(output)
    [{'__type__': 'update', 'label': 'Text 0', 'value': '谢谢这个啊，王茉莉队长要健康快乐'}, 
    {'__type__': 'update', 'label': 'Text 1', 'value': '谢谢这个啊，王茉莉队长要健康快乐。 谢谢你。'}, 
    {'__type__': 'update', 'label': 'Text 2', 'value': '谢谢这个啊，王茉莉队长要健康快乐。 谢谢你。'}, 
    {'__type__': 'update', 'label': 'Text', 'value': ''}, 
    {'__type__': 'update', 'label': 'Text', 'value': ''}, 
    {'__type__': 'update', 'label': 'Text', 'value': ''}, 
    {'__type__': 'update', 'label': 'Text', 'value': ''}, 
    {'__type__': 'update', 'label': 'Text', 'value': ''}, 
    {'__type__': 'update', 'label': 'Text', 'value': ''}, {
    '__type__': 'update', 'label': 'Text', 'value': ''}, 
    'data/test/9.11.wav', 'data/test\\9.11_01.wav', 
    'data/test\\9.11_01_00.wav', None, None, None, None, None, None, None, False, False, False, False, False, False, False, False, False, False]
    '''
    return output


def b_next_index(index, batch):
    b_save_file()
    if (index + batch) <= g_max_json_index:
        return index + batch, *b_change_index(index + batch, batch)
    else:
        return index, *b_change_index(index, batch)


def b_previous_index(index, batch):
    b_save_file()
    if (index - batch) >= 0:
        return index - batch, *b_change_index(index - batch, batch)
    else:
        return 0, *b_change_index(0, batch)


def b_submit_change(*text_list):
    '''
    检查这一batch的textbox中的内容是否与记录的有变化,如果有则写入全局变量,并写入文件

    Args:
        本batch文本列表
    
    Returns:
        g_index:全局变量,当前batch索引头
        *b_change_index(g_index, g_batch):用于更新页面文本,音频,选中勾的字典数组

    '''
    #print(text_list)
    #('谢谢这个啊， 乐。 谢谢你。 ', '谢谢这个啊，王茉莉队长要健康快乐。 谢谢你。 ', '谢谢这个啊，王茉莉队长要健康快乐。 谢谢你。 ', '', '', '', '', '', '', '')
    global g_data_json
    change = False

    for i, new_text in enumerate(text_list):
        if g_index + i <= g_max_json_index:
            new_text = new_text.strip() + " "
            if g_data_json[g_index + i][g_json_key_text] != new_text:#{'wav_path': 'data/test/9.11.wav', 'speaker_name': 'test', 'language': 'ZH', 'text': '谢谢这个啊， 乐。 谢谢你。'}
                g_data_json[g_index + i][g_json_key_text] = new_text
                change = True
    if change:
        b_save_file()
    return g_index, *b_change_index(g_index, g_batch)

def save_and_next_index(index,batch,*text_list,):
    global g_data_json
    change = False

    for i, new_text in enumerate(text_list):
        if g_index + i <= g_max_json_index:
            new_text = new_text.strip() + " "
            if g_data_json[g_index + i][g_json_key_text] != new_text:#{'wav_path': 'data/test/9.11.wav', 'speaker_name': 'test', 'language': 'ZH', 'text': '谢谢这个啊， 乐。 谢谢你。'}
                g_data_json[g_index + i][g_json_key_text] = new_text
                change = True
    if change:
        b_save_file()

    if (index + batch) <= g_max_json_index:
        return index + batch, *b_change_index(index + batch, batch)
    else:
        return index, *b_change_index(index, batch)
    


    

def b_delete_audio(*checkbox_list):
    '''
        从g_data_json中删除当前batch选中的元素,调整g_max_json_index和g_index,并写入文件

    Args:
        本batch选中状态的bool元组
    
    Returns:
        用于修改index滑块的json
        用于更新页面文本,音频,选中勾的字典数组


    '''
    #print(checkbox_list) (False, False, True, False, False, False, False, False, False, False)
    global g_data_json, g_index, g_max_json_index
    b_save_file()#将全局变量的值写入文件
    change = False
    for i, checkbox in reversed(list(enumerate(checkbox_list))):#reversed从后往前遍历
        if g_index + i < len(g_data_json):#排除最后一batch剩余的空白
            if checkbox == True:
                path=g_data_json[g_index + i][g_json_key_path]
                if os.path.exists(path):
                    os.remove(path)
                g_data_json.pop(g_index + i)#删除数组当前batch第i个元素
                change = True

    g_max_json_index = len(g_data_json) - 1
    if g_index > g_max_json_index:
        g_index = g_max_json_index
        g_index = g_index if g_index >= 0 else 0
    if change:
        b_save_file()
    # return gr.Slider(value=g_index, maximum=(g_max_json_index if g_max_json_index>=0 else 0)), *b_change_index(g_index, g_batch)
    return {
        "value": g_index,
        "__type__": "update",
        "maximum": (g_max_json_index if g_max_json_index >= 0 else 0),
    }, *b_change_index(g_index, g_batch)


def b_invert_selection(*checkbox_list):
    new_list = [not item if item is True else True for item in checkbox_list]
    return new_list


def get_next_path(filename):
    base_dir = os.path.dirname(filename)#获得路径
    base_name = os.path.splitext(os.path.basename(filename))[0]#获得无后缀文件名
    for i in range(100):
        new_path = os.path.join(base_dir, f"{base_name}_{str(i).zfill(2)}.wav")#组合路径和文件名
        if not os.path.exists(new_path):
            return new_path
    return os.path.join(base_dir, f"{str(uuid.uuid4())}.wav")

def b_save_and_audio_cut(start_percent,end_percent,*checkbox_list_and_text_list):

    '''裁剪a%到b%音频并保存'''
    global g_data_json, g_max_json_index
    if start_percent>=end_percent:
        return {"__type__": "update","value": 0},{"__type__": "update","value": 1},{"value": g_index, "maximum": g_max_json_index, "__type__": "update"},*b_change_index(g_index, g_batch)
    
    #分离被打包到一起的checkbox_list_and_text_list
    mid = len(checkbox_list_and_text_list) // 2
    checkbox_list=checkbox_list_and_text_list[:mid]
    text_list=checkbox_list_and_text_list[mid:]

    change = False
    for i, new_text in enumerate(text_list):
        if g_index + i <= g_max_json_index:
            new_text = new_text.strip() + " "
            if g_data_json[g_index + i][g_json_key_text] != new_text:#{'wav_path': 'data/test/9.11.wav', 'speaker_name': 'test', 'language': 'ZH', 'text': '谢谢这个啊， 乐。 谢谢你。'}
                g_data_json[g_index + i][g_json_key_text] = new_text
                change = True
    if change:
        b_save_file()
    

    checked_index = []
    for i, checkbox in enumerate(checkbox_list):
        if checkbox == True and g_index + i < len(g_data_json):
            checked_index.append(g_index + i)#获得勾选的语音的全局索引

    if len(checked_index) == 1:
        index = checked_index[0]
        audio_json = copy.deepcopy(g_data_json[index])#拷贝一份当前语音{'wav_path': 'data/test/9.11.wav', 'speaker_name': 'test', 'language': 'ZH', 'text': '谢谢这个啊， 乐。 谢谢你。'}
        path = audio_json[g_json_key_path]
        data, sample_rate = librosa.load(path, sr=None, mono=True)
        audio_maxframe = len(data)
        start_frame = int(start_percent*audio_maxframe)#秒数×采样率(帧/秒)
        end_frame=int(end_percent*audio_maxframe)

        audio_cuted = data[start_frame:end_frame]
        soundfile.write(path, audio_cuted, sample_rate)#写入原始文件名
        b_save_file()

    g_max_json_index = len(g_data_json) - 1#更新长度
    return {"__type__": "update","value": 0},{"__type__": "update","value": 1},{"value": g_index, "maximum": g_max_json_index, "__type__": "update"},*b_change_index(g_index, g_batch)

def b_audio_split(audio_breakpoint, *checkbox_list):
    global g_data_json, g_max_json_index
    checked_index = []
    for i, checkbox in enumerate(checkbox_list):
        if checkbox == True and g_index + i < len(g_data_json):
            checked_index.append(g_index + i)#获得勾选的语音的全局索引
    if len(checked_index) == 1:
        index = checked_index[0]
        audio_json = copy.deepcopy(g_data_json[index])#拷贝一份当前语音{'wav_path': 'data/test/9.11.wav', 'speaker_name': 'test', 'language': 'ZH', 'text': '谢谢这个啊， 乐。 谢谢你。'}
        path = audio_json[g_json_key_path]
        data, sample_rate = librosa.load(path, sr=None, mono=True)
        audio_maxframe = len(data)
        break_frame = int(audio_breakpoint * sample_rate)#秒数×采样率

        if break_frame >= 1 and break_frame < audio_maxframe:
            audio_first = data[0:break_frame]
            audio_second = data[break_frame:]
            nextpath = get_next_path(path)#获得新的音频文件名
            soundfile.write(nextpath, audio_second, sample_rate)#后半段写入新文件名
            soundfile.write(path, audio_first, sample_rate)#前半段写入原始文件名
            g_data_json.insert(index + 1, audio_json)#插入新的
            g_data_json[index + 1][g_json_key_path] = nextpath#修改新插入的信息的地址
            b_save_file()

    g_max_json_index = len(g_data_json) - 1#更新长度
    # return gr.Slider(value=g_index, maximum=g_max_json_index), *b_change_index(g_index, g_batch)
    return {"value": g_index, "maximum": g_max_json_index, "__type__": "update"}, *b_change_index(g_index, g_batch)


def b_merge_audio(interval_r, *checkbox_list):
    global g_data_json, g_max_json_index
    b_save_file()
    checked_index = []
    audios_path = []
    audios_text = []
    for i, checkbox in enumerate(checkbox_list):
        if checkbox == True and g_index + i < len(g_data_json):
            checked_index.append(g_index + i)

    if len(checked_index) > 1:
        for i in checked_index:
            audios_path.append(g_data_json[i][g_json_key_path])
            audios_text.append(g_data_json[i][g_json_key_text])
        for i in reversed(checked_index[1:]):
            g_data_json.pop(i)

        base_index = checked_index[0]
        base_path = audios_path[0]
        g_data_json[base_index][g_json_key_text] = "".join(audios_text)

        audio_list = []
        l_sample_rate = None
        for i, path in enumerate(audios_path):
            data, sample_rate = librosa.load(path, sr=l_sample_rate, mono=True)
            l_sample_rate = sample_rate
            if i > 0:
                silence = np.zeros(int(l_sample_rate * interval_r))
                audio_list.append(silence)

            audio_list.append(data)

        audio_concat = np.concatenate(audio_list)

        soundfile.write(base_path, audio_concat, l_sample_rate)

        b_save_file()

    g_max_json_index = len(g_data_json) - 1

    # return gr.Slider(value=g_index, maximum=g_max_json_index), *b_change_index(g_index, g_batch)
    return {"value": g_index, "maximum": g_max_json_index, "__type__": "update"}, *b_change_index(g_index, g_batch)


def b_save_json():
    with open(g_load_file, "w", encoding="utf-8") as file:
        for data in g_data_json:
            file.write(f"{json.dumps(data, ensure_ascii=False)}\n")


def b_save_list():
    '''
    将全局变量g_data_json中存储的所有数据,覆写进原文件
    '''
    with open(g_load_file, "w", encoding="utf-8") as file:
        for data in g_data_json:
            wav_path = data["wav_path"]
            speaker_name = data["speaker_name"]
            language = data["language"]
            text = data["text"]
            file.write(f"{wav_path}|{speaker_name}|{language}|{text}".strip() + "\n")


def b_load_json():
    global g_data_json, g_max_json_index
    with open(g_load_file, "r", encoding="utf-8") as file:
        g_data_json = file.readlines()
        g_data_json = [json.loads(line) for line in g_data_json]
        g_max_json_index = len(g_data_json) - 1


def b_load_list():
    '''
    从list文件读取数据,存入全局变量g_data_json,并修改g_max_json_index
    '''

    global g_data_json, g_max_json_index
    with open(g_load_file, "r", encoding="utf-8") as source:
        data_list = source.readlines()
        for _ in data_list:
            data = _.split("|")
            if len(data) == 4:
                wav_path, speaker_name, language, text = data
                g_data_json.append(
                    {"wav_path": wav_path, "speaker_name": speaker_name, "language": language, "text": text.strip()}
                )
            else:
                print("error line:", data)
        g_max_json_index = len(g_data_json) - 1


def b_save_file():
    '''
    将全局变量g_data_json中存储的所有数据,覆写进原文件
    '''
    if g_load_format == "json":
        b_save_json()
    elif g_load_format == "list":
        b_save_list()


def b_load_file():
    if g_load_format == "json":
        b_load_json()
    elif g_load_format == "list":
        b_load_list()


def set_global(load_json, load_list, json_key_text, json_key_path, batch):
    global g_json_key_text, g_json_key_path, g_load_file, g_load_format, g_batch

    g_batch = int(batch)

    if load_json != "None":
        g_load_format = "json"
        g_load_file = load_json
    elif load_list != "None":
        g_load_format = "list"
        g_load_file = load_list
    else:
        g_load_format = "list"
        g_load_file = "data/test.list"

    g_json_key_text = json_key_text
    g_json_key_path = json_key_path

    b_load_file()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--load_json", default="None", help="source file, like demo.json")
    parser.add_argument("--is_share", default="False", help="whether webui is_share=True")
    parser.add_argument("--load_list", default="None", help="source file, like demo.list")
    parser.add_argument("--webui_port_subfix", default=8080, help="source file, like demo.list")
    parser.add_argument("--json_key_text", default="text", help="the text key name in json, Default: text")
    parser.add_argument("--json_key_path", default="wav_path", help="the path key name in json, Default: wav_path")
    parser.add_argument("--g_batch", default=10, help="max number g_batch wav to display, Default: 10")

    args = parser.parse_args()

    set_global(args.load_json, args.load_list, args.json_key_text, args.json_key_path, args.g_batch)

    with gr.Blocks() as demo:
        with gr.Row():
            btn_merge_audio = gr.Button("合并音频")
            btn_delete_audio = gr.Button("删除音频")
            btn_save_json = gr.Button("保存文件", visible=True)
            btn_invert_selection = gr.Button("反选")
            btn_submit_change = gr.Button("提交文本")
            btn_previous_index = gr.Button("上批索引")
            btn_next_index = gr.Button("下批索引")

        with gr.Row():
            with gr.Column(scale=5,min_width=250):
                with gr.Row():
                    with gr.Column(scale=1,min_width=90):
                        btn_change_index = gr.Button("跳转索引")
                        btn_audio_split = gr.Button("分割音频")
                    with gr.Column(scale=4,min_width=160):
                        index_slider = gr.Slider(minimum=0, maximum=g_max_json_index, value=g_index, step=1, label="跳转索引", scale=3)
                        splitpoint_slider = gr.Slider(minimum=0, maximum=120.0, value=0, step=0.1, label="音频分割点(s)", scale=3)
                
            with gr.Column(scale=5,min_width=160):
                slider_start = gr.Slider(minimum=0, maximum=1, step=0.01, label="开始百分比位置",interactive=True)
                slider_end = gr.Slider(minimum=0, maximum=1, step=0.01, label="结束百分比位置",value=1,interactive=True)

            with gr.Column(scale=1,min_width=100):
                btn_audio_cut=gr.Button("提交并裁剪音频")


        with gr.Row():
            with gr.Column():
                for _ in range(0, g_batch):
                    with gr.Row(): 
                        with gr.Column(scale=5,min_width=160):
                            text = gr.Textbox(label="Text", visible=True)
                            g_text_list.append(text)
                        with gr.Column(scale=5,min_width=160):
                            audio_output = gr.Audio(label="Output Audio", visible=True)
                            g_audio_list.append(audio_output)               
                        with gr.Column(scale=1,min_width=90):
                            audio_check = gr.Checkbox(label="Yes", show_label=True, info="选中")
                            g_checkbox_list.append(audio_check)#(False, False, True, False, False, False, False, False, False, False)


                               
        with gr.Row():

            batchsize_slider = gr.Slider(
                minimum=1, maximum=g_batch, value=g_batch, step=1, label="Batch Size", scale=3, interactive=False
            )
            interval_slider = gr.Slider(minimum=0, maximum=2, value=0, step=0.01, label="Interval", scale=3)

            with gr.Column(scale=1):
                btn_theme_dark = gr.Button("Light Theme", link="?__theme=light", scale=1)
                btn_theme_light = gr.Button("Dark Theme", link="?__theme=dark", scale=1)               
            with gr.Column(scale=1):
                btn_save_and_next_index=gr.Button("提交并下批索引")


        btn_save_and_next_index.click(
            save_and_next_index,
            inputs=[
                index_slider,
                batchsize_slider, 
                *g_text_list       
            ],
            outputs=[index_slider,*g_text_list, *g_audio_list, *g_checkbox_list]
        )

        btn_change_index.click(
            b_change_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=[*g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_submit_change.click(
            b_submit_change,
            inputs=[
                *g_text_list,
            ],
            outputs=[index_slider, *g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_previous_index.click(
            b_previous_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=[index_slider, *g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_next_index.click(
            b_next_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=[index_slider, *g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_delete_audio.click(
            b_delete_audio,
            inputs=[*g_checkbox_list],
            outputs=[index_slider, *g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_merge_audio.click(
            b_merge_audio,
            inputs=[interval_slider, *g_checkbox_list],
            outputs=[index_slider, *g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_audio_cut.click(
            b_save_and_audio_cut,
            inputs=[slider_start,slider_end,*g_checkbox_list,*g_text_list],
            outputs=[slider_start,slider_end,index_slider,*g_text_list, *g_audio_list, *g_checkbox_list]
        )

        btn_audio_split.click(
            b_audio_split,
            inputs=[splitpoint_slider, *g_checkbox_list],#裁剪点和所有勾选组件
            outputs=[index_slider, *g_text_list, *g_audio_list, *g_checkbox_list],
        )

        btn_invert_selection.click(b_invert_selection, inputs=[*g_checkbox_list], outputs=[*g_checkbox_list])

        btn_save_json.click(b_save_file)

        demo.load(
            b_change_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=[*g_text_list, *g_audio_list, *g_checkbox_list],
        )

    demo.launch(
        server_name="0.0.0.0",
        inbrowser=True,
        quiet=True,
        share=eval(args.is_share),
        server_port=int(args.webui_port_subfix),
    )
