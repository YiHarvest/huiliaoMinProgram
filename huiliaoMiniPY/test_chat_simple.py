import socket
import time

def test_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 8020))
        sock.close()
        
        if result == 0:
            print('端口 8020 可以连接')
            return True
        else:
            print(f'端口 8020 连接失败，错误码: {result}')
            return False
    except Exception as e:
        print(f'连接测试失败: {e}')
        return False

if __name__ == '__main__':
    print('开始测试连接...')
    for i in range(5):
        if test_connection():
            print('测试成功！')
            break
        print(f'等待服务启动... ({i+1}/5)')
        time.sleep(2)
