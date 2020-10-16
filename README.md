# dingtouhuice
可以回测基金收益，用Python实现的后台服务

# 前提
安装好Python3
安装好pip
安装好gunicorn

# 使用方法

pip install pandas
pip install xalpha

gunicorn dingTouHuiCheDjango.wsgi -b 0.0.0.0:8080
