# test_axon_serve.py

import logging
from hetu.axon import Axon
from hetu.synapse import Synapse
from hetu.hetu import Hetutensor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 测试请求格式
class TestRequest(Synapse):
    message: str

class TestResponse(Synapse):
    reply: str

# 处理函数
async def handle_request(request: TestRequest) -> TestResponse:
    return TestResponse(reply=f"Received: {request.message}")

def test_serve():
    """测试 Axon 的链上服务功能"""
    
    # 1. 创建 Hetutensor 客户端
    logging.info("Creating Hetutensor client...")
    hetu = Hetutensor(
        username="hanbo",
        password="lhb1999114",
        log_verbose=True  # 启用详细日志
    )
    
    try:
        # 2. 检查钱包
        wallet_address = hetu.get_wallet_address()
        logging.info(f"Wallet address: {wallet_address}")
        
        # 3. 获取可用的子网
        total_subnets = hetu.get_total_subnets()
        subnet_ids = hetu.get_subnets()
        logging.info(f"Total subnets: {total_subnets}")
        logging.info(f"Available subnets: {subnet_ids}")
        
        # 选择第一个子网进行测试
        test_netuid = subnet_ids[0] if subnet_ids else 1
        logging.info(f"Testing with netuid: {test_netuid}")
        
        # 4. 检查当前注册状态
        is_registered = hetu.is_neuron(test_netuid, wallet_address)
        logging.info(f"Already registered on subnet {test_netuid}: {is_registered}")
        
        # 5. 创建 Axon 服务器
        axon = Axon(
            username="hanbo",
            password="lhb1999114",
            ip="127.0.0.1",
            port=8091,
            max_workers=4,
            trace=True
        )
        
        # 6. 注册处理函数
        axon.attach(
            forward_fn=handle_request
        )
        
        # 7. 启动服务（这会触发链上注册或更新）
        logging.info(f"Starting Axon service on subnet {test_netuid}...")
        axon.serve(netuid=test_netuid, hetutensor=hetu)
        
        # 8. 验证注册状态
        is_registered_after = hetu.is_neuron(test_netuid, wallet_address)
        logging.info(f"Registration status after serve: {is_registered_after}")
        
        if is_registered_after:
            # 9. 获取神经元信息
            neuron_info = hetu.get_neuron_info(test_netuid, wallet_address)
            if neuron_info:
                logging.info("Neuron info:")
                logging.info(f"  Active: {neuron_info['is_active']}")
                logging.info(f"  Validator: {neuron_info['is_validator']}")
                logging.info(f"  Axon endpoint: {neuron_info['axon_endpoint']}:{neuron_info['axon_port']}")
        
        # 10. 打印测试命令
        logging.info("\nTest commands:")
        logging.info("""
curl -X POST http://127.0.0.1:8091/ping -H "Content-Type: application/json" -d '{}'

curl -X POST http://127.0.0.1:8091/ -H "Content-Type: application/json" -d '{
    "message": "Hello from client"
}'
        """)
        
        # 保持服务运行
        logging.info("\nServer is running. Press Ctrl+C to stop.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopping server...")
            axon.stop()
            
    except Exception as e:
        logging.error(f"Error during test: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
    finally:
        hetu.close()

if __name__ == "__main__":
    test_serve()