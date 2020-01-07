# 图片上传的扩展
from qiniu import Auth, put_data

access_key = ""  # 你的七牛云AccessKey
secret_key = ""  # 你的七牛云SecretKey
bucket_name = ""  # 存储空间名


def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
    except Exception as e:
        raise e
    if info and info.status_code != 200:
        raise Exception("上传文件失败")
    return ret["key"]


if __name__ == '__main__':
    file_name = input("输入上传的文件")
    with open(file_name, "rb") as f:
        storage(f.read())