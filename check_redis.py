import redis
import logging
import sys
import time
import socket
import subprocess
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def fix_redis_persistence():
    """修复Redis持久化问题"""
    try:
        # 首先尝试使用redis-cli直接修复
        try:
            subprocess.run([
                'redis-cli', 'config', 'set', 'save', '""'
            ], check=True, capture_output=True)
            subprocess.run([
                'redis-cli', 'config', 'set', 'appendonly', 'no'
            ], check=True, capture_output=True)
            subprocess.run([
                'redis-cli', 'config', 'rewrite'
            ], check=True, capture_output=True)
            logging.info("通过redis-cli修复Redis持久化配置成功")
            return True
        except subprocess.CalledProcessError:
            logging.warning("通过redis-cli修复失败，尝试修改配置文件...")

        # 如果redis-cli方式失败，尝试直接修改配置文件
        redis_conf_paths = [
            r'C:\Program Files\Redis\redis.windows.conf',
            r'C:\Program Files\Redis\redis.conf',
            r'C:\Redis\redis.windows.conf'
        ]
        
        conf_path = None
        for path in redis_conf_paths:
            if os.path.exists(path):
                conf_path = path
                break
        
        if not conf_path:
            logging.error("未找到Redis配置文件")
            return False
            
        # 读取当前配置
        with open(conf_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 修改配置
        new_lines = []
        for line in lines:
            if line.startswith('save '):
                continue  # 跳过所有save配置
            elif line.startswith('appendonly '):
                new_lines.append('appendonly no\n')
            else:
                new_lines.append(line)
        
        # 添加新的save配置（禁用RDB）
        new_lines.append('save ""\n')
        
        # 备份原配置文件
        backup_path = conf_path + '.backup'
        try:
            os.replace(conf_path, backup_path)
            logging.info(f"原配置文件已备份到: {backup_path}")
        except Exception as e:
            logging.error(f"备份配置文件失败: {str(e)}")
            return False
        
        # 写入新配置
        try:
            with open(conf_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logging.info("Redis配置文件已更新")
            
            # 重启Redis服务
            if restart_redis_windows():
                logging.info("Redis服务已重启，配置生效")
                return True
            else:
                # 如果重启失败，恢复备份
                os.replace(backup_path, conf_path)
                logging.error("Redis重启失败，已恢复原配置")
                return False
                
        except Exception as e:
            logging.error(f"写入新配置失败: {str(e)}")
            # 恢复备份
            os.replace(backup_path, conf_path)
            logging.info("已恢复原配置")
            return False
            
    except Exception as e:
        logging.error(f"修复Redis持久化配置失败: {str(e)}")
        return False

def restart_redis_windows():
    """重启Windows下的Redis服务"""
    try:
        # 停止服务
        subprocess.run(['net', 'stop', 'Redis'], check=False)
        time.sleep(2)
        
        # 启动服务
        subprocess.run(['net', 'start', 'Redis'], check=True)
        time.sleep(2)
        logging.info("Redis服务已重启")
        return True
    except Exception as e:
        logging.error(f"重启Redis服务失败: {str(e)}")
        return False

def check_redis_connection(max_retries=3, retry_delay=2):
    """
    检查Redis连接状态
    :param max_retries: 最大重试次数
    :param retry_delay: 重试间隔（秒）
    :return: (bool, str) - (是否连接成功, 状态信息)
    """
    for attempt in range(max_retries):
        try:
            # 检查端口占用
            if is_port_in_use(6379):
                logging.warning("端口6379已被占用，可能是Redis已在运行或被其他程序占用")
            
            # 尝试连接Redis
            client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=1,
                socket_keepalive=True,
                retry_on_timeout=True
            )
            
            try:
                # 测试连接
                client.ping()
            except redis.exceptions.ResponseError as e:
                if "MISCONF" in str(e):
                    logging.warning("检测到Redis持久化配置问题，尝试修复...")
                    if fix_redis_persistence():
                        logging.info("正在重启Redis服务...")
                        if restart_redis_windows():
                            continue  # 重试连接
            
            # 测试基本操作
            test_key = "test_connection"
            client.set(test_key, "test_value")
            client.delete(test_key)
            
            logging.info("Redis连接成功且工作正常")
            return True, "连接成功"
            
        except redis.ConnectionError as e:
            logging.error(f"连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                return False, f"连接失败: {str(e)}"
                
        except redis.RedisError as e:
            logging.error(f"Redis错误: {str(e)}")
            return False, f"Redis错误: {str(e)}"
            
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            return False, f"未知错误: {str(e)}"

def diagnose_redis():
    """诊断Redis问题"""
    logging.info("开始Redis诊断...")
    
    # 检查端口
    if is_port_in_use(6379):
        logging.warning("端口6379被占用")
        logging.info("请检查:")
        logging.info("1. Redis是否已经在运行")
        logging.info("2. 是否有其他程序占用了6379端口")
    else:
        logging.info("端口6379未被占用")
    
    # 尝试连接
    success, message = check_redis_connection()
    if not success:
        logging.error("Redis连接诊断失败")
        logging.info("建议操作:")
        logging.info("1. 确认Redis服务是否已启动")
        logging.info("2. 检查Redis配置文件")
        logging.info("3. 尝试重启Redis服务")
        logging.info("4. 检查防火墙设置")
    else:
        logging.info("Redis诊断完成，一切正常")

if __name__ == "__main__":
    try:
        logging.info("开始Redis连接检查...")
        success, message = check_redis_connection()
        if not success:
            logging.error(f"Redis连接失败: {message}")
            diagnose_redis()
        else:
            logging.info("Redis连接检查完成，状态正常")
    except KeyboardInterrupt:
        logging.info("检查被用户中断")
    except Exception as e:
        logging.error(f"检查过程发生错误: {str(e)}") 