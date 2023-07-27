import logging
import pyautogui
import subprocess
import random
import shutil
import game
import json
import account
import utils
import api
from time import sleep
from constants import *
from vo.Summoner import Summoner
from dao import dao
from vo.GiftInfo import GiftInfo
log = logging.getLogger(__name__)

connection = api.Connection()
riotConnection = api.RiotConnection()
giftConnection = api.SendGiftConnection()

class ClientError(Exception):
    pass

class AccountLeveled(Exception):
    pass

def init():
    # Ensure game config file is correct，
    log.info("覆盖配置文件")
    # 判断英雄联盟游戏目录下配置文件是否存在
    if os.path.exists(LEAGUE_GAME_CONFIG_PATH):
        # 存在则把它覆盖过去
        shutil.copyfile(LOCAL_GAME_CONFIG_PATH, LEAGUE_GAME_CONFIG_PATH)
    else:
        # 不存在则复制过去
        shutil.copy2(LOCAL_GAME_CONFIG_PATH, LEAGUE_GAME_CONFIG_PATH)

    # Get account username and password
    username = account.get_username()
    password = account.get_password()

    # Start league
    log.info("开始启动登陆界面，并尝试登陆")
    start_app(username, password)

    # 初始化连接 Connect to api
    connection.init()
    sleep(3)
    # 检查更新
    patcher()
    sleep(2)
    # 初始化拳头客户端连接
    riotConnection.init()
    # 初始化送礼连接
    giftConnection.init(connection.lcu_port, connection.token)

# Main Control Loop
def loop():
    previous_phase = ''
    errno = 0

    giveGift("ckjkihhg","斗魂觉醒 羽量级战利品",10)

    '''while True:
        #获取当前游戏的阶段
        phase = get_phase()
        log.debug("阶段为: {}".format(phase))
        # 如果和之前的阶段相同，15 次获取阶段都不会改变
        if phase == previous_phase:
            errno += 1
            log.debug("Phase same as previous. Errno {}".format(errno))
            if errno == 15:
                log.warning("Transition error. Phase will not change.")
                raise ClientError
        else:
            errno = 0
        # 阶段匹配
        match phase:
            # 刚登陆的时候是没有大厅的，所以先创建大厅
            case 'None':
                create_default_lobby(GAME_LOBBY_ID)
            # 开启对局，寻找对战，执行完成后进入下一阶段
            case 'Lobby':
                start_matchmaking(GAME_LOBBY_ID)
            # 如果当前阶段是寻找对局中
            case 'Matchmaking':
                queue()
            case 'ReadyCheck':
                accept_match()
            case 'ChampSelect':
                handle_game_lobby()
            case 'InProgress':
                game.play_game()
            case 'Reconnect':
                reconnect()
            case 'WaitingForStats':
                wait_for_stats()
            case 'PreEndOfGame':
                pre_end_of_game()
            case 'EndOfGame':
                end_of_game()
            case _:
                log.warning("Unknown phase: {}".format(phase))
                raise ClientError

        previous_phase = phase
        sleep(2)'''



# 获取商城域名
def getStore():
    for i in range(5):
        r = connection.request('get','/lol-store/v1/getStoreUrl')
        if r.status_code == 200:
            return r.content
    log.info("获取商城域名失败")
    return False

# 查询登陆者的信息
def getCurrentSummonerInfo():
    for i in range(4):
        try:
            log.info("第 {} 次尝试获取登陆者的信息".format(i))
            r = connection.request('get','/lol-summoner/v1/current-summoner')
            if r.status_code == 200:
                summonerJson = r.json()
                summoner = Summoner();
                summoner.summonerName  = summonerJson['displayName']
                summoner.summonerLevel = summonerJson['summonerLevel']
                summoner.summonerExp   = str(summonerJson['xpSinceLastLevel']) + "/" + str(summonerJson['xpUntilNextLevel'])
                summoner.profileIconId = summonerJson['profileIconId']
                summoner.summonerId    = summonerJson['summonerId']
                summoner.accountId     = summonerJson['accountId']
                summoner.puuid         = summonerJson['puuid']
                summoner.RP            = getRP()
                return summoner
        except:
            return False
    return False

# 查询召唤师的信息
def getSummonerInfo(summonerName):
    for i in range(5):
        r = connection.request('get','/lol-summoner/v1/summoners?name=' + summonerName)
        if r.status_code == 200:
            summonerJson = r.json()
            summoner = Summoner();
            summoner.summonerName  = summonerJson['displayName']
            summoner.summonerLevel = summonerJson['summonerLevel']
            summoner.summonerExp   = str(summonerJson['xpSinceLastLevel']) + "/" + str(summonerJson['xpUntilNextLevel'])
            summoner.profileIconId = summonerJson['profileIconId']
            summoner.summonerId    = summonerJson['summonerId']
            summoner.accountId     = summonerJson['accountId']
            summoner.puuid         = summonerJson['puuid']
            return summoner
    return False

# 获取账号的剩余点券
def getRP():
    for i in range(10):
        r = connection.request('get', '/lol-inventory/v1/wallet/RP')
        if r.status_code == 200:
            return r.json()['RP']
    return False

# 添加好友 （拳头客户端 api）
def addFriend(data):
    for i in range(10):
        r = riotConnection.request('post','/chat/v4/friendrequests',data=data)
        if r.status_code == 200:
            print(r.json)
            return True
    return False


# 查询正在申请的好友列表 (拳头客户端 api)
def queryFriend():
    for i in range(3):
        r = connection.request('get','/chat/v4/friendrequests')
        if r.status_code == 200:
            return r.json()
    log.info("查询已申请好友列表失败")
    raise ClientError

# 赠送礼物
def giveGift(FriendName, giftName, giftAmount):
    with open('data.json', 'r', encoding='utf-8') as f:
        giftData = json.load(f)
    if giftData == None:
        log.info("礼物数据打开失败")
        return False

    # 查询好友信息
    summonerInfo = getSummonerInfo(FriendName)
    if summonerInfo == False:
        log.info("玩家：" + FriendName + "信息疑似不存在或者网络错误")
        return False

    # 查询商城的名字， 并且去除字符串前后的 ""
    storeName = getStore().decode('utf-8')[1:-1]
    if storeName == False:
        log.info("玩家：" + FriendName + "商城地址获取失败")
        return False

    # 获取个人信息
    currentSummonerInfo = getCurrentSummonerInfo()
    if currentSummonerInfo == False:
        log.info("登陆账号的个人信息获取失败")
        return False

    # 获取礼物信息
    giftInfo = getGiftInfoFromJson(giftData[giftName], giftName)
    # 这里计算有点小问题
    if giftInfo.RP * giftAmount < currentSummonerInfo.RP:
        log.info("玩家 {} 剩余的点券为 {} ， 不足以买 {} 个 {}".format(FriendName, currentSummonerInfo.RP, giftName, giftAmount))
        return False

    # 送礼
    giveGiftApi(currentSummonerInfo.accountId, summonerInfo.summonerId, giftInfo, storeName, giftAmount)




def giveGiftApi(accountId, friendId, giftInfo, storeName, giftAmount):

    data = {
        'customMessage' : '留言已使我耳不忍聞',
        'receiverSummonerId' : friendId,
        'giftItemId' : giftInfo.id,
        'accountId' : accountId,
        'items' : [
            {
                'inventoryType' : giftInfo.inventoryType,
                'itemId' : giftInfo.itemId,
                'ipCost' : None,
                'rpCost' : giftInfo.RP,
                'quantity' : giftAmount
            }
        ]
    }

    giftConnection.request(data, storeName)



    pass

# 从 json 中拿出礼物的数据
def getGiftInfoFromJson(giftData, giftName):
    giftInfo = GiftInfo()
    giftInfo.giftName = giftName
    giftInfo.id = giftData['Id']
    giftInfo.itemId = giftData['itemId']
    giftInfo.inventoryType = giftData['inventoryType']
    giftInfo.RP = giftData["rp"]
    return giftInfo

# 创建默认的
def create_default_lobby(lobby_id):
    log.info("用大厅的 id 创建大厅: {}".format(lobby_id))
    connection.request('post', '/lol-lobby/v2/lobby', data={'queueId': lobby_id})
    sleep(1.5)


# 开始进行游戏匹配的操作
def start_matchmaking(lobby_id):
    log.info("Starting queue for lobby_id: {}".format(lobby_id))
    r = connection.request('get', '/lol-lobby/v2/lobby')
    # 如果返回的大厅 id 和我们自己的大厅 id 不同，就创建我们 id 的大厅
    if r.json()['gameConfig']['queueId'] != lobby_id:
        create_default_lobby(lobby_id)
        sleep(1)
    # 然后开启对局，寻找对战
    connection.request('post', '/lol-lobby/v2/lobby/matchmaking/search')
    sleep(1.5)

    # Check for dodge timer
    r = connection.request('get', '/lol-matchmaking/v1/search')
    if r.status_code == 200 and len(r.json()['errors']) != 0:
        dodge_timer = int(r.json()['errors'][0]['penaltyTimeRemaining'])
        log.info("Dodge Timer. Time Remaining: {}".format(utils.seconds_to_min_sec(dodge_timer)))
        sleep(dodge_timer)

# 一直寻找对局，直到找到对局
def queue():
    log.info("In queue. Waiting for match.")
    while True:
        if get_phase() != 'Matchmaking':
            return
        sleep(1)

# 接受匹配
def accept_match():
    log.info("Accepting match")
    connection.request('post', '/lol-matchmaking/v1/ready-check/accept')


# 在客户端拦截游戏
def handle_game_lobby():
    log.debug("Lobby State: INITIAL. Time Left in Lobby: 90s. Action: Initialize.")
    r = connection.request('get', '/lol-champ-select/v1/session')
    if r.status_code != 200:
        return
    cs = r.json()

    r2 = connection.request('get', '/lol-lobby-team-builder/champ-select/v1/pickable-champion-ids')
    if r2.status_code != 200:
        return
    f2p = r2.json()

    champ_index = 0
    f2p_index = 0
    requested = False
    while r.status_code == 200:
        lobby_state = cs['timer']['phase']
        lobby_time_left = int(float(cs['timer']['adjustedTimeLeftInPhase']) / 1000)

        # Find player action
        for action in cs['actions'][0]:  # There are 5 actions in the first action index, one for each player
            if action['actorCellId'] != cs['localPlayerCellId']:  # determine which action corresponds to bot
                continue

            # Check if champ is already locked in
            if not action['completed']:
                # Select Champ or Lock in champ that has already been selected
                if action['championId'] == 0:  # no champ selected, attempt to select a champ
                    log.info("Lobby State: {}. Time Left in Lobby: {}s. Action: Hovering champ.".format(lobby_state, lobby_time_left))

                    if champ_index < len(CHAMPS):
                        champion_id = CHAMPS[champ_index]
                        champ_index += 1
                    else:
                        champion_id = f2p[f2p_index]
                        f2p_index += 1

                    url = '/lol-champ-select/v1/session/actions/{}'.format(action['id'])
                    data = {'championId': champion_id}
                    connection.request('patch', url, data=data)
                else:  # champ selected, lock in
                    log.info("Lobby State: {}. Time Left in Lobby: {}s. Action: Locking in champ.".format(lobby_state, lobby_time_left))
                    url = '/lol-champ-select/v1/session/actions/{}'.format(action['id'])
                    data = {'championId': action['championId']}
                    connection.request('post', url + '/complete', data=data)

                    # Ask for mid
                    if not requested:
                        sleep(1)
                        chat(random.choice(ASK_4_MID_DIALOG), 'handle_game_lobby')
                        requested = True
            else:
                log.debug("Lobby State: {}. Time Left in Lobby: {}s. Action: Waiting".format(lobby_state, lobby_time_left))
            r = connection.request('get', '/lol-champ-select/v1/session')
            if r.status_code != 200:
                log.info('Lobby State: CLOSED. Time Left in Lobby: 0s. Action: Exit.')
                return
            cs = r.json()
            sleep(3)


# 重新连接
def reconnect():
    for i in range(3):
        r = connection.request('post', '/lol-gameflow/v1/reconnect')
        if r.status_code == 204:
            return
        sleep(2)
    log.warning('Could not reconnect to game')

# Often times disconnects will happen after a game finishes. The client will indefinitely return
# the phase 'WaitingForStats'
def wait_for_stats():
    log.info("Waiting for stats.")
    for i in range(60):
        sleep(2)
        if get_phase() != 'WaitingForStats':
            return
    log.warning("Waiting for stats timeout.")
    raise ClientError

# Handles game client reopening, honoring teammates, clearing level up rewards and mission rewards
# This func should hopefully be updated to not include any clicking, but im not sure of any endpoints that clear
# the 'send email' popup or mission/level rewards
# 在游戏结束前
def pre_end_of_game():
    log.info("Honoring teammates and accepting rewards.")
    sleep(3)
    # occasionally the lcu-api will be ready before the actual client window appears
    # in this instance, the utils.click will throw an exception. just catch and wait
    try:
        utils.click(POPUP_SEND_EMAIL_X_RATIO, LEAGUE_CLIENT_WINNAME, 1)
        sleep(1)
        honor_player()
        sleep(2)
        utils.click(POPUP_SEND_EMAIL_X_RATIO, LEAGUE_CLIENT_WINNAME, 1)
        sleep(1)
        for i in range(3):
            utils.click(POST_GAME_SELECT_CHAMP_RATIO, LEAGUE_CLIENT_WINNAME, 1)
            utils.click(POST_GAME_OK_RATIO, LEAGUE_CLIENT_WINNAME, 1)
        utils.click(POPUP_SEND_EMAIL_X_RATIO, LEAGUE_CLIENT_WINNAME, 1)
    except:
        sleep(3)

# Checks account level before returning to lobby， 在游戏结束后
def end_of_game():
    account_level = get_account_level()
    if account_level < ACCOUNT_MAX_LEVEL:
        log.info("ACCOUNT LEVEL: {}. Returning to game lobby.\n".format(account_level))
        connection.request('post', '/lol-lobby/v2/play-again')
        sleep(2)

        # Occasionally, posting to the play-again endpoint just does not work
        post = True
        for i in range(15):
            if get_phase() != 'EndOfGame':
                return
            if post:
                connection.request('post', '/lol-lobby/v2/play-again')
            else:
                create_default_lobby(GAME_LOBBY_ID)
            post = not post
            sleep(1)
        log.warning("Could not exit play-again screen.")
        raise ClientError
    else:
        log.info("SUCCESS: Account Leveled")
        raise AccountLeveled


# UTILITY FUNCS

def start_app(username, password):
    # 如果游戏在运行，直接返回
    if is_league_running():
        log.info("已经有游戏正在运行了")
        return
    log.info("启动 league of legend")
    # 启动游戏，应该是打开登陆界面
    subprocess.run([LEAGUE_PATH])
    time_out = 0
    prior_login = True
    waiting = False
    while True:
        # 三十秒 登陆界面还启动不起来
        if time_out == 30:
            log.error("登陆界面无法启动")
            raise ClientError
        # 游戏界面是否存在，如果游戏界面存在
        if utils.exists(LEAGUE_CLIENT_WINNAME):
            # 有游戏界面，但是没有登陆界面，不就意味着游戏已经通过上一次打开了嘛
            if prior_login:
                log.info("登陆界面不存在")
            # 如果有登陆界面就把它关掉
            else:
                log.info("游戏界面已经成功启动，接下来关闭登陆界面")
                output = subprocess.check_output(KILL_RIOT_CLIENT, shell=False)
                log.info(str(output, 'gb18030').rstrip())
            sleep(5)
            return
        # 登陆界面是否存在，不存在才需要输入账号密码
        if utils.exists(RIOT_CLIENT_WINNAME):
            # 没
            if not waiting:
                log.info("客户端已经打开了，接下来执行登陆逻辑")
                prior_login = False
                waiting = True
                time_out = 0
                # 获取登陆界面窗口
                pyautogui.getWindowsWithTitle(RIOT_CLIENT_WINNAME)
                log.info("获取到了窗口的句柄")
                sleep(3)
                pyautogui.typewrite(username)
                sleep(2)
                pyautogui.press('tab')
                sleep(3)
                pyautogui.typewrite(password)
                sleep(1)
                # 点击回车
                pyautogui.press('enter')
                sleep(5)
            else:
                log.debug("Waiting for league to open...")
                sleep(1)
                pyautogui.press('enter')  # sometimes the riot client will force you to press 'play'
        # 不存在就休息一秒钟
        sleep(1)
        # 秒数 + 1
        time_out += 1

def patcher():
    log.info("Checking for Client Updates")
    r = connection.request('get', '/patcher/v1/products/league_of_legends/state')
    if r.status_code != 200:
        return
    logged = False
    while not r.json()['isUpToDate']:
        if not logged:
            log.info("Client is patching...")
            logged = True
        sleep(3)
        r = connection.request('get', '/patcher/v1/products/league_of_legends/state')
        log.debug('Status Code: {}, Percent Patched: {}%'.format(r.status_code, r.json()['percentPatched']))
        log.debug(r.json())
    log.info("Client is up to date!")


# 关闭游戏
def close():
    log.info("Terminating league related processes.")
    os.system(KILL_LEAGUE)
    os.system(KILL_LEAGUE_CLIENT)
    os.system(KILL_RIOT_CLIENT)
    sleep(5)

# 判断游戏是否在运行
def is_league_running():
    res = subprocess.check_output(["TASKLIST"], creationflags=0x08000000)
    output = str(res)
    # 英雄联盟客户端运行时，会产生运行时文件 "LeagueClient.exe", "League of Legends.exe"
    for name in PROCESS_NAMES:
        if name in output:
            return True
    return False

#
def honor_player():
    for i in range(3):
        r = connection.request('get', '/lol-honor-v2/v1/ballot')
        if r.status_code == 200:
            players = r.json()['eligiblePlayers']
            index = random.randint(0, len(players)-1)
            connection.request('post', '/lol-honor-v2/v1/honor-player', data={"summonerId": players[index]['summonerId']})
            log.info("Honor Success: Player {}. Champ: {}. Summoner: {}. ID: {}".format(index+1, players[index]['championName'], players[index]['summonerName'], players[index]['summonerId']))
            return
        sleep(2)
    log.info('Honor Failure. Player -1, Champ: NULL. Summoner: NULL. ID: -1')
    connection.request('post', '/lol-honor-v2/v1/honor-player', data={"summonerId": 0})  # will clear honor screen


# 看样子像是聊天
def chat(msg, calling_func_name=''):
    chat_id = ''
    r = connection.request('get', '/lol-chat/v1/conversations')
    if r.status_code != 200:
        if calling_func_name != '':
            log.warning("{} chat attempt failed. Could not reach endpoint".format(calling_func_name))
        else:
            log.warning("Could not reach endpoint")
        return

    for convo in r.json():
        if convo['gameName'] != '' and convo['gameTag'] != '':
            continue
        chat_id = convo['id']

    if chat_id == '':
        if calling_func_name != '':
            log.warning('{} chat attempt failed. Could not send message. Chat ID is Null'.format(calling_func_name))
        else:
            log.warning('Could not send message. Chat ID is Null')
        return

    data = {"body": msg}
    r = connection.request('post', '/lol-chat/v1/conversations/{}/messages'.format(chat_id), data=data)
    if r.status_code != 200:
        if calling_func_name != '':
            log.warning('{}, could not send message. HTTP STATUS: {} - {}'.format(calling_func_name, r.status_code, r.json()))
        else:
            log.warning('Could not send message. HTTP STATUS: {} - {}'.format(r.status_code, r.json()))
    else:
        if calling_func_name != '':
            log.debug("{}, message success. Msg: {}".format(calling_func_name, msg))
        else:
            log.debug("Message Success. Msg: {}".format(msg))


# 获取阶段
def get_phase():
    for i in range(15):
        r = connection.request('get', '/lol-gameflow/v1/gameflow-phase')
        if r.status_code == 200:
            return r.json()
        sleep(1)
    log.warning("Could not get phase.")
    raise ClientError


# 我感觉是获取账号等级
def get_account_level():
    for i in range(3):
        r = connection.request('get', '/lol-chat/v1/me')
        if r.status_code == 200:
            level = r.json()['lol']['level']
            return int(level)
        sleep(1)
    log.warning('Could not reach endpoint')

