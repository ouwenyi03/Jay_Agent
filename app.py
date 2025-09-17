import os
import json
import time
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import shutil  # 新增：用于删除文件和文件夹

# 初始化Flask应用
app = Flask(__name__)

# 加载环境变量
load_dotenv()

# 配置
ALIYUN_API_KEY = os.getenv('ALIYUN_API_KEY')
ALIYUN_API_SECRET = os.getenv('ALIYUN_API_SECRET')
ALIYUN_ENDPOINT = "dashscope.aliyuncs.com"  # 阿里云API端点


def initialize_data_files():
    """初始化数据文件和文件夹，处理可能的文件冲突"""
    # 处理jay_data文件夹
    if os.path.exists('jay_data'):
        if not os.path.isdir('jay_data'):
            # 如果存在同名文件，先删除
            os.remove('jay_data')
            os.makedirs('jay_data')
    else:
        os.makedirs('jay_data')

    # 处理conversations文件夹
    if os.path.exists('conversations'):
        if not os.path.isdir('conversations'):
            # 如果存在同名文件，先删除
            os.remove('conversations')
            os.makedirs('conversations')
    else:
        os.makedirs('conversations')

    # 初始化明星数据文件
    STAR_DATA_FILE = 'jay_data/posts.json'
    if not os.path.exists(STAR_DATA_FILE):
        with open(STAR_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)

    # 初始化对话历史文件
    DEFAULT_CONVERSATION_FILE = 'conversations/default.json'
    if not os.path.exists(DEFAULT_CONVERSATION_FILE):
        with open(DEFAULT_CONVERSATION_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)


# 初始化数据文件和文件夹
initialize_data_files()


def crawl_star_social_media():
    """爬取明星社交媒体内容（使用模拟数据）"""
    STAR_DATA_FILE = 'jay_data/posts.json'
    # 检查是否已有数据，如果有则不重复爬取
    if os.path.getsize(STAR_DATA_FILE) > 0:
        with open(STAR_DATA_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            if len(existing_data) > 0:
                print("已有明星数据，无需重新爬取")
                return existing_data

    # 模拟爬取周杰伦的社交媒体内容
    simulated_posts = [
        {"content": "新专辑制作中，敬请期待！哎哟不错哦～", "date": "2023-10-15"},
        {"content": "今天和弹头、宇豪一起创作，怀念以前的时光", "date": "2023-10-10"},
        {"content": "篮球是我的爱好，音乐是我的生命", "date": "2023-09-28"},
        {"content": "谢谢大家支持我的电影，接下来会有更多惊喜", "date": "2023-09-15"},
        {"content": "给女儿写了首歌，希望她以后会喜欢", "date": "2023-09-05"},
        {"content": "华语音乐需要更多创新，我会继续努力", "date": "2023-08-20"},
        {"content": "演唱会的歌单正在确定中，你们最想听哪首？", "date": "2023-08-10"},
        {"content": "怀念刚出道的时候，那时候的冲劲很足", "date": "2023-07-25"}
    ]

    # 保存爬取的数据
    with open(STAR_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(simulated_posts, f, ensure_ascii=False, indent=2)

    print("已获取明星社交媒体数据")
    return simulated_posts


def get_chat_history():
    """获取对话历史"""
    DEFAULT_CONVERSATION_FILE = 'conversations/default.json'
    with open(DEFAULT_CONVERSATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_chat_history(history):
    """保存对话历史"""
    DEFAULT_CONVERSATION_FILE = 'conversations/default.json'
    with open(DEFAULT_CONVERSATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def call_aliyun_api(prompt):
    """调用阿里云通义千问API（修正版）"""
    try:
        # 通义千问的正确API地址（参考官方文档）
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ALIYUN_API_KEY}"  # 仅需API_KEY
        }

        # 修正请求数据格式（按官方规范）
        data = {
            "model": "qwen-plus",  # 模型名称
            "input": {
                "messages": [
                    {"role": "system", "content": "你是周杰伦的AI分身，模拟他的说话风格"},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": 0.8,
                "max_tokens": 500
            }
        }

        response = requests.post(url, headers=headers, json=data)

        # 先检查响应状态码
        if response.status_code != 200:
            print(f"API请求失败，状态码: {response.status_code}")
            print(f"错误内容: {response.text}")  # 打印错误详情用于调试
            return "抱歉，暂时无法回复，稍后再试~"

        response_data = response.json()

        # 修正响应解析逻辑（按官方返回格式）
        if "output" in response_data and "text" in response_data["output"]:
            return response_data["output"]["text"]
        else:
            print("API返回格式异常:", response_data)
            return "抱歉，我没听清楚，可以再问一次吗？"

    except json.JSONDecodeError:
        print("API返回非JSON内容:", response.text)  # 打印非JSON响应
        return "抱歉，网络有点小问题，稍后再聊吧～"
    except Exception as e:
        print(f"API调用错误: {str(e)}")
        return "抱歉，网络有点小问题，稍后再聊吧～"



def generate_prompt(user_message, star_posts, chat_history):
    """生成提示词，包含明星风格信息、历史对话和当前消息"""
    # 提取明星说话风格特点
    style_points = """
    你是周杰伦（Jay Chou），需要模仿他的说话风格:
    1. 常用口头禅："哎哟不错哦"、"屌"、"蛮酷的"、"这样子"
    2. 说话带点台湾腔，语气轻松随意
    3. 经常提到音乐创作、篮球、电影、家人等话题
    4. 回答简洁有力，不会说太多客套话
    5. 会用幽默风趣的方式回应问题
    6. 提到自己的作品时会带有自信但不傲慢
    """

    # 构建明星近期动态信息
    recent_posts = "\n".join([f"- {post['content']}" for post in star_posts[:3]])
    star_context = f"周杰伦近期动态：\n{recent_posts}\n"

    # 构建对话历史上下文
    history_context = ""
    if chat_history:
        history_context = "对话历史：\n"
        for msg in chat_history[-5:]:  # 只取最近5条历史
            history_context += f"用户：{msg['user']}\n周杰伦：{msg['ai']}\n"

    # 构建完整提示词
    prompt = f"""
    {style_points}

    {star_context}

    {history_context}

    现在用户说：{user_message}

    请以周杰伦的身份和语气回复用户，保持自然，不要太长：
    """

    return prompt


@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天API接口"""
    user_message = request.json.get('message', '')

    if not user_message:
        return jsonify({"response": "请输入内容再发送哦！"})

    # 1. 获取明星数据
    star_posts = crawl_star_social_media()

    # 2. 获取对话历史
    chat_history = get_chat_history()

    # 3. 生成提示词
    prompt = generate_prompt(user_message, star_posts, chat_history)

    # 4. 调用阿里云API
    ai_response = call_aliyun_api(prompt)

    # 5. 保存对话到历史记录
    chat_history.append({
        "user": user_message,
        "ai": ai_response,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_chat_history(chat_history)

    return jsonify({"response": ai_response})


if __name__ == '__main__':
    # 启动服务，debug=True便于开发调试
    app.run(debug=True)
