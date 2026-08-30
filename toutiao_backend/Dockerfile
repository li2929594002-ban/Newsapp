FROM python:3.11-slim
WORKDIR /app

# 先装依赖再拷代码（代码改了不用重装依赖，利用构建缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]