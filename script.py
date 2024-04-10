import os
import requests
import yaml
import re
import json
import shutil
import random
from time import sleep

def dir_is_exists(directory, pattern):
    """
    在指定目录中搜索与正则表达式匹配的文件名。
    :param directory: 要搜索的目录
    :param pattern: 文件名匹配的正则表达式
    :return: 是否成功匹配
    """
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            if re.search(pattern+"-tmdb-", dir):
                return True
    return False

def print_result(count, fail, already, fail_list):
    """
    打印结果
    :param count: 成功搬运的文件数
    :param fail: 失败搬运的文件数
    :param already: 已经存在的文件数
    :param fail_list: 失败搬运的文件列表
    """
    print(f"{GREEN}[Info]{RESET}: Successfully moved " + f"{YELLOW}{count}{RESET}" + " actors")
    print(f"{GREEN}[Info]{RESET}: Already exists " + f"{YELLOW}{already}{RESET}" + " actors")
    print(f"{GREEN}[Info]{RESET}: Failed to move " + f"{YELLOW}{fail}{RESET}" + " actors")
    if fail > 0:
        print(f"{GREEN}[Info]{RESET}: Failed list: ", fail_list)


if __name__ == '__main__':

    RED = '\033[31m'  # 红色
    GREEN = '\033[32m'  # 绿色
    YELLOW = '\033[33m'  # 黄色
    RESET = '\033[0m'  # 重置颜色

    with open('config.yaml', 'r', encoding='utf-8') as f:
        Config = yaml.safe_load(f)
    
    sleep_time = 0

    if Config.get('path', {}).get('source') is None or Config.get('path', {}).get('target') == None:
        print(f"{RED}[Error]{RESET}: Please set the source and target path in config.yaml")
        exit(1)
    if Config.get('tmdb-api', {}).get('API-key') is None:
        print(f"{RED}[Error]{RESET}: Please set the tmdb api key in config.yaml")
        exit(1)
    api_key = Config['tmdb-api']['API-key']

    if Config.get('proxy', {}).get('http') != None:
        os.environ['http_proxy'] = Config['proxy']['http']
    if Config.get('proxy', {}).get('https') != None:
        os.environ['https_proxy'] = Config['proxy']['https']
    sleep_time = 0
    if Config.get('sleep') != None:
        sleep_time = Config['sleep']


    source = Config['path']['source']
    target = Config['path']['target']

    url_prev = "https://api.themoviedb.org/3/search/person?"
    query_params = ""
    other_params = "&include_adult=false&language=en-US&page=1"

    headers = {
        "accept": "application/json",
        "Authorization": api_key
    }



    count = 0
    fail = 0
    already = 0
    fail_list = []

    for root, dirs, files in os.walk(source):
        if '.actors' in dirs:
            actor_dir = os.path.join(root, '.actors')
            # print(actor_dir)
            for file in os.listdir(actor_dir):
                if file.endswith('.jpg'):
                    prev_actor_name = file.split('.')[0]
                    actor_name = prev_actor_name.replace('_', ' ')
                    encoded_name = requests.utils.requote_uri(actor_name)
                    
                    # 获取首字母
                    first_letter = actor_name[0].lower()
                    target_path = target + "/" + first_letter
                    
                    # 如果首字母子文件夹还不存在，就创建
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)

                    # 如果这个演员已经存在，就不再进行搬运
                    if dir_is_exists(target_path, actor_name):
                        print(actor_name + " exists")
                        continue

                    tmdb_id = ""
                    query_params = "query=" + encoded_name
                    url = url_prev + query_params + other_params

                    response = requests.get(url, headers=headers)
                    # response是json格式的，需要解析
                    response_result = json.loads(response.text).get('results', {})
                    if response_result is None or not response_result:
                        print(f"{RED}[Error]{RESET}: " + YELLOW + actor_name + RESET + " not found in tmdb database")
                        fail += 1
                        fail_list.append(actor_name)
                        continue

                    tmdb_id = response_result[0].get('id', {})
                    if tmdb_id == None:
                        print(f"{RED}[Error]{RESET}: " + YELLOW + actor_name + RESET + " not found in tmdb database")
                        fail += 1
                        fail_list.append(actor_name)
                        continue
                    
                    
                    actor_full_path = actor_name + "-tmdb-" + str(tmdb_id)
                    target_full_path = target_path + "/" + actor_full_path

                    if not os.path.exists(target_full_path):
                        os.makedirs(target_full_path)
                    
                    # 将file移动到target_full_path
                    shutil.move(os.path.join(actor_dir, file), os.path.join(target_full_path, file))
                    # rename
                    os.rename(os.path.join(target_full_path, file), os.path.join(target_full_path, "folder.jpg"))

                    print(f"{GREEN}[Info]{RESET}: Successfully moved Actor " + f"{YELLOW}{actor_name}{RESET}" + " \
                          in " + YELLOW + root + RESET + " to " + YELLOW + target_full_path + RESET)

                    count += 1
                    if sleep_time != 0:
                        sleep(sleep_time + random.uniform(0, 1))

    print_result(count, fail, already, fail_list)
