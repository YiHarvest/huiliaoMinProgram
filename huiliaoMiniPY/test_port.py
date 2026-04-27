import socket

def test_port(port):
    try:
        # 创建一个socket对象
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置超时时间
        sock.settimeout(2)
        # 尝试绑定端口
        sock.bind(('127.0.0.1', port))
        # 关闭socket
        sock.close()
        print(f'端口 {port} 可用')
        return True
    except OSError as e:
        print(f'端口 {port} 不可用: {e}')
        return False

if __name__ == '__main__':
    # 测试8020端口
    test_port(8020)
    # 测试8010端口
    test_port(8010)
