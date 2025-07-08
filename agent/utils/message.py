import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

from .logger import logger
from .shareConfig import get_config

def send_byPushplus(text: str):
    dp = get_config()
    token = dp.getValue("pushplus_token")
    if token == None or token == "":
        logger.info("未配置pushplus_token")
        return
    rootUrl = f"http://www.pushplus.plus/send?token={token}"
    title="MaaGumballs"
    request_url = rootUrl+"&title="+title+"&content="+text
    try:
        response = requests.get(request_url)
        if response.status_code == 200:
            if response.json()["code"] == 200:
                logger.info("推送成功")
            else:
                logger.info("推送失败")
        else:
            logger.error("推送失败")
    except Exception as e:
        logger.info(f"pushplus发送失败：{e}")
        return
def send_email(text: str):
    dp = get_config()
    # 邮件配置
    send_email = dp.getValue("send_email")
    receiver_email = dp.getValue("receiver_email")
    password = dp.getValue("smtp_key")
    smtp_server = dp.getValue("smtp_server")
    smtp_port = dp.getValue("smtp_port")
    
    if send_email and receiver_email and password and smtp_server and smtp_port:
        # 创建邮件内容
        message = MIMEMultipart()
        message["From"] = send_email
        message["To"] = receiver_email
        message["Subject"] = "MaaGumballs"

        # 添加邮件正文
        message.attach(MIMEText(text, "plain"))

        # 连接 SMTP 服务器并发送邮件
        try:
            # 使用 SMTP_SSL 建立安全连接
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.login(send_email, password)
            text = message.as_string()
            server.sendmail(send_email, receiver_email, text)
            server.quit()
            logger.info("邮件发送成功！")
        except Exception as e:
            logger.info(f"邮件发送失败: {e}")
    else:
        logger.info("未配置邮件发送，请检查配置文件！")
        
def send_message(text: str):
    dp = get_config()
    message_type = dp.getValue("message_type")
    if message_type :
        if message_type == "email":
            send_email(text)
        elif message_type == "pushplus":
            send_byPushplus(text)
        else:
            logger.info("未配置消息类型或暂不支持此消息类型！")
    else:
        logger.info("未配置消息发送，请检查配置文件！")