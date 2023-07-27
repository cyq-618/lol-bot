import logging
import os
import re

import psutil
import win32api

log = logging.getLogger(__name__)

"""
获取所有进程
"""


def get_process():
    # 获取当前所有的进程
    pids = psutil.pids()
    for pid in pids:
        p = psutil.Process(pid)
        process_name = p.name()
        print("Process name is: %s, pid is: %s" % (process_name, pid))


"""
    通过进程名判断该进程是否存在
"""


def is_exist_process(process_name):
    # print("待查找的进程：" + process_name)
    pids = psutil.pids()
    for pid in pids:
        p = psutil.Process(pid)
        if p.name() == process_name:
            return True
    else:
        return False


"""
    通过进程名查找进程pid
"""


def creat_process_by_name(process_name):
    pids = psutil.pids()
    try:
        for pid in pids:
            p = psutil.Process(pid)
            if p.name() == process_name:
                return p
        return None
    except psutil.NoSuchProcess as e:
        print(e)


"""
    查找进程RiotClientUx.exe
"""


def find_rcu_process():
    for process in psutil.process_iter():
        if process.name() in ['RiotClientUx.exe', 'RiotClientUx']:
            return process
    return None


"""
    通过进程名杀死进程
    taskkill /F /IM explorer.exe
"""


def kill_process_by_name(name):
    log.info(f"杀死进程：{name}")
    cmd = rf'taskkill /F /IM "{name}"'
    os.system(cmd)


"""
通过进程名启动一个进程
"""


def start_process(name):
    os.system(name)


"""
根据exe文件名启动一个进程（非系统exe须带路径）
"""


def exec_process(exe_dir, exe_name):
    win32api.ShellExecute(0, 'open', exe_dir, '', '', 1)
    pids = psutil.pids()
    for pid in pids:
        if psutil.Process(pid).name() == exe_name:
            return {"pid": pid}


# 统计某一个进程名所占用的内存，同一个进程名，可能有多个进程
def count_process_memoey(process_name):
    pattern = re.compile(r'(\S+)\s+(\d+)\s.*\s(\S+\sK)')
    cmd = 'tasklist /fi "imagename eq ' + process_name + '"' + ' | findstr.exe ' + '"' + process_name + '"'
    # findstr后面的程序名加上引号防止出现程序带有空格
    result = os.popen(cmd).read()
    result_list = result.split("\n")
    full_memory = 0.0
    for src_line in result_list:
        src_line = "".join(src_line.split('\n'))
        if len(src_line) == 0:
            break
        m = pattern.search(src_line)
        if m is None:
            continue
        # 由于是查看python进程所占内存，因此通过pid将本程序过滤掉
        if str(os.getpid()) == m.group(2):
            continue
        ori_mem = m.group(3).replace(',', '')
        ori_mem = ori_mem.replace(' K', '')
        ori_mem = ori_mem.replace(r'\sK', '')
        mem_each = int(ori_mem)
        full_memory += mem_each * 1.0 / 1024
        # print('ProcessName:' + m.group(1) + '\tPID:' + m.group(2) + '\tmemory size:%.2f' % (mem_each * 1.0 / 1024), 'M')
        # print(time.ctime())  # 打印当前的时间
    print(f"进程{process_name}共占用内存：{full_memory}M")
    log.info(f"进程{process_name}共占用内存：{full_memory}M")
    return full_memory
