import subprocess
import os
import requests
import json
import argparse
import toml

home = os.environ['HOME']
config = toml.load(f'{home}/.siuu/conf/conf.toml')
port = config["server"]["port"]
http_port = config["server"]["http"]["port"]
socks_port = config["server"]["socks"]["port"]

# url
URL_GET_PROXIES = f'http://127.0.0.1:{port}/prx'
URL_GET_PROXY = f'http://127.0.0.1:{port}/prx/get'
URL_SET_DEFAULT_PROXY = f'http://127.0.0.1:{port}/prx/set'
URL_GET_DEFAULT_PROXY = f'http://127.0.0.1:{port}/prx/get-default'
URL_TEST_PROXY_DELAY = f'http://127.0.0.1:{port}/prx/delay'
URL_RELATED_ROUTES = f'http://127.0.0.1:{port}'


def get_proxies(key=None) -> str:
    resp = requests.get(f"{URL_GET_PROXIES}?prx={key}" if key else URL_GET_PROXIES)
    if resp.status_code != 200:
        return json.dumps({"items": []})

    data = resp.json()

    # 生成 items 列表
    result = {
        "items": [
            {
                "title": f"{proxy['Name']}{' (selected)' if idx == 0 else ''}",
                "subtitle": f"{proxy['Type']} - {proxy['Server']}:{proxy['Port']}",
                "arg": f"{proxy['Name']}",
                "valid": False if idx == 0 else True,
                "icon": {
                    "path": "icons/proxy.png" if idx > 0 else "icons/default.png"
                }
            }
            for idx, proxy in enumerate(data)
        ]
    }

    return json.dumps(result)


def get_proxy(name: str) -> str:
    resp = requests.get(f"{URL_GET_PROXY}?prx={name}")
    if resp.status_code != 200:
        return json.dumps({"items": []})

    proxy = resp.json()

    # 确保 proxy 是字典
    if not isinstance(proxy, dict):
        return json.dumps({"items": []})

    result = {
        "items": [
            {
                "title": f"{k}: {v}",
                "subtitle": "press enter to to copy to clipboard",
                "arg": f"{v}",
                "valid": True,
                "icon": {
                    "path": "icons/option_prx.png"
                }
            }
            for k, v in proxy.items()
        ]
    }

    result['items'] = [
                          {
                              "title": "Set Default Proxy",
                              "arg": f"set,{proxy['Name']}",
                              "valid": True,
                              "icon": {
                                  "path": "icons/set_default.png"
                              }
                          }
                      ] + result['items']

    return json.dumps(result)


def set_default_prx(args):
    requests.get(f'{URL_SET_DEFAULT_PROXY}?proxy={args.proxy}')


def test_proxy_delay(args):
    icon_status_ok = "icons/status_ok.png"
    icon_status_fail = "icons/status_fail.png"

    result = {"items": []}
    resp = requests.get(
        f"{URL_TEST_PROXY_DELAY}?prx={args.prx}" if args.prx else URL_TEST_PROXY_DELAY)
    if resp.status_code == 200:
        data = resp.json()

        # 获取默认代理
        resp = requests.post(URL_GET_DEFAULT_PROXY)
        default = resp.text if resp.status_code == 200 else None
        dd = data.pop(default)
        # 构造 items 列表
        result["items"] = [
            {
                "title": f"{default} (selected)",
                "subtitle": f"{int(dd * 1000)}ms" if 0 < dd < 1 else "timeout",
                "arg": f"{default}",
                "icon": {
                    "path": icon_status_ok if 0 <= dd < 1 else icon_status_fail
                }
            }
        ] if default else []

        dd = data.get('direct', None)
        result["items"] += [
            {
                "title": "direct",
                "subtitle": f"{int(dd * 1000)}ms",
                "arg": "direct",
                "icon": {
                    "path": icon_status_ok if 0 <= dd < 1 else icon_status_fail
                }
            }
        ] if "direct" in data else []

        data.pop("direct", None)

        result["items"] += [
            {
                "title": f"{k} :",
                "subtitle": f"{int(v * 1000)}ms" if 0 < v < 1 else "timeout",
                "arg": k,
                "icon": {
                    "path": icon_status_ok if 0 < v < 1 else icon_status_fail
                }
            }
            for k, v in data.items()
        ]

    print(json.dumps(result))


def turn_proxy(args):
    prx_host = "127.0.0.1"
    pass_domains = [
        "192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.1", "localhost", "*.local", "timestamp.apple.com"
    ]

    network = 'WI-FI'

    if args.state == 'on':
        subprocess.run(["networksetup", "-setproxybypassdomains", network, *pass_domains])
        subprocess.run(["networksetup", "-setwebproxy", network, prx_host, str(http_port)])
        subprocess.run(["networksetup", "-setsecurewebproxy", network, prx_host, str(http_port)])
        subprocess.run(["networksetup", "-setsocksfirewallproxy", network, prx_host, str(socks_port)])

        subprocess.run(["networksetup", "-setwebproxystate", network, "on"])
        subprocess.run(["networksetup", "-setsecurewebproxystate", network, "on"])
        subprocess.run(["networksetup", "-setsocksfirewallproxystate", network, "on"])

    elif args.state == 'off':
        subprocess.run(["networksetup", "-setwebproxystate", network, "off"])
        subprocess.run(["networksetup", "-setsecurewebproxystate", network, "off"])
        subprocess.run(["networksetup", "-setsocksfirewallproxystate", network, "off"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple proxy")

    # 参数护持组
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--keyword", "-key", nargs="?", help="关键字", default=None)
    group.add_argument("--name", "-n", nargs="?", help="名称", default=None)

    subparsers = parser.add_subparsers(dest="command")

    # set 子命令
    set_parser = subparsers.add_parser("set", help="设置默认代理")
    set_parser.add_argument("proxy", help="要设置的默认代理")
    set_parser.set_defaults(func=set_default_prx)

    # turn 子命令
    turn_parser = subparsers.add_parser("turn", help="控制代理开关")
    turn_parser.add_argument("state", choices=["on", "off"], help="代理开关: on 或 off")
    turn_parser.set_defaults(func=turn_proxy)

    # test 子命令
    test_parser = subparsers.add_parser("test", help="测试延迟")
    test_parser.add_argument("prx", nargs="?", help="测试的代理，模糊匹配", default=None)
    test_parser.set_defaults(func=test_proxy_delay)

    args = parser.parse_args()

    # 处理逻辑
    if args.command == "set":
        args.func(args)  # 处理 set 命令
    elif args.command == "turn":
        args.func(args)  # 处理 turn 命令
    elif args.command == "test":
        args.func(args)  # 处理 test 命令
    elif args.name is not None:
        print(get_proxy(args.name))  # 精确查找
    elif args.keyword is not None:
        print(get_proxies(args.keyword))  # 处理模糊匹配
    else:
        print(get_proxies())
