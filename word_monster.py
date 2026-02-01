import pygame
import random
import sys
import time
import math

# 尝试导入文本转语音模块
try:
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    # 设置语速（-10到10，默认为0）
    speaker.Rate = 0  # 加快语速
    HAS_TTS = True
except:
    HAS_TTS = False  # 如果没有安装win32com，禁用TTS功能

# 初始化Pygame
pygame.init()
# 初始化音效系统
pygame.mixer.init()

# 设置游戏窗口为自适应大小，覆盖大部分显示器并保留关闭按钮
display_info = pygame.display.Info()
# 获取显示器分辨率
SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h
# 设置窗口大小为显示器的90%，确保窗口标题栏和边框可见
WIDTH, HEIGHT = int(SCREEN_WIDTH * 0.9), int(SCREEN_HEIGHT * 0.9)
WIN = pygame.display.set_mode((WIDTH, HEIGHT))  # 不使用pygame.FULLSCREEN参数
pygame.display.set_caption("单词怪物追赶游戏")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 游戏难度设置
DIFFICULTY = {
    "easy": {
        "monster_speed": 1,  # 减慢怪物速度
        "bullet_vel": 0.3,  # 子弹速度与怪物速度一致
        "spawn_rate": 200
    },
    "medium": {
        "monster_speed": 1.5,
        "bullet_vel": 0.5,  # 子弹速度与怪物速度一致
        "spawn_rate": 150
    },
    "hard": {
        "monster_speed": 2,
        "bullet_vel": 0.7,  # 子弹速度与怪物速度一致
        "spawn_rate": 100
    }
}
current_difficulty = "easy"  # 默认难度
is_fullscreen = False  # 全屏状态

# 字体设置
FONT = pygame.font.SysFont('SimHei', 30)
SMALL_FONT = pygame.font.SysFont('SimHei', 20)

# 玩家设置
PLAYER_SIZE = 40
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 8
ATTACK_RANGE = 1800  # 攻击范围（像素）

# 子弹设置
bullets = []
bullet_speed = 10

# 单词列表（英文和中文对照）
WORD_LIST = []

# 读取和解析考研单词文件
def load_kaoyan_words():
    global WORD_LIST
    try:
        with open('d:\\qlib\\word_monster_game\\kaoyan_words.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line:
                    # 尝试用制表符分割（新格式：单词\t释义\t英文例句\t中文例句）
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        english_word = parts[0]
                        meaning = parts[1]
                        # 如果有例句，添加到列表
                        if len(parts) >= 4:
                            en_sentence = parts[2]
                            cn_sentence = parts[3]
                            WORD_LIST.append([english_word, meaning, en_sentence, cn_sentence])
                        else:
                            # 旧格式，只提取中文释义
                            chinese_word = ''
                            for char in meaning:
                                if '\u4e00' <= char <= '\u9fff':
                                    chinese_word += char
                            if chinese_word:
                                WORD_LIST.append([english_word, chinese_word, "", ""])
        # 尝试读取github_words.txt（新格式）
        try:
            with open('d:\\qlib\\word_monster_game\\github_words.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        # 新格式：单词\t释义\t英文例句\t中文例句
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            english_word = parts[0]
                            meaning = parts[1]
                            en_sentence = parts[2]
                            cn_sentence = parts[3]
                            WORD_LIST.append([english_word, meaning, en_sentence, cn_sentence])
        except FileNotFoundError:
            pass
        # 尝试读取github_words.txt（新格式）
        try:
            with open('d:\\qlib\\word_monster_game\\github_words.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        # 新格式：单词\t释义\t英文例句\t中文例句
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            english_word = parts[0]
                            meaning = parts[1]
                            en_sentence = parts[2]
                            cn_sentence = parts[3]
                            WORD_LIST.append([english_word, meaning, en_sentence, cn_sentence])
        except FileNotFoundError:
            pass

    except Exception as e:
        print(f"读取单词文件失败: {e}")
        # 使用默认单词列表
        WORD_LIST = [["apple", "苹果"], ["banana", "香蕉"], ["cherry", "樱桃"], ["orange", "橙子"], ["grape", "葡萄"], 
                     ["watermelon", "西瓜"], ["strawberry", "草莓"], ["pineapple", "菠萝"], ["mango", "芒果"], ["peach", "桃子"],
                     ["computer", "电脑"], ["keyboard", "键盘"], ["mouse", "鼠标"], ["monitor", "显示器"], ["printer", "打印机"], 
                     ["speaker", "音箱"], ["headphone", "耳机"], ["laptop", "笔记本"], ["tablet", "平板"], ["phone", "手机"],
                     ["python", "蟒蛇"], ["java", "咖啡"], ["c++", "C加加"], ["javascript", "脚本"], ["html", "超文本"], 
                     ["css", "样式表"], ["ruby", "红宝石"], ["php", "超文本"], ["swift", "迅捷"], ["kotlin", "科特林"]]

# 加载考研单词
load_kaoyan_words()

# 怪物设置
monsters = []
monster_base_size = 30  # 怪物基础大小

# 游戏状态
score = 0
game_over = False
last_shot_time = 0  # 上一次发射的时间
BULLET_COOLDOWN = 0.5  # 子弹冷却时间（秒）
last_tts_time = 0  # 上一次TTS调用的时间
TTS_COOLDOWN = 3  # TTS冷却时间（秒）
tts_language_toggle = 0  # TTS语言切换：0=中文，1=英文
clip_bullets = []  # 弹夹中的子弹内容
PLAYER_SPEED = 5  # 玩家移动速度
next_bullet_word = ""  # 即将发射的子弹内容
last_bullet_word_update = 0  # 上一次更新子弹内容的时间
BULLET_WORD_UPDATE_INTERVAL = 6  # 子弹内容更新间隔（秒）

# 技能系统
SKILL_COOLDOWN = 3  # 技能冷却时间（秒）
skills = {
    "freeze": {
        "name": "冰冻",
        "last_used": 0,
        "active": False,
        "duration": 3  # 冰冻持续时间（秒）
    },
    "firestorm": {
        "name": "火焰风暴",
        "last_used": 0,
        "active": False,
        "duration": 2  # 火焰持续时间（秒）
    },
    "lightning": {
        "name": "闪电链",
        "last_used": 0,
        "active": False,
        "duration": 0.5  # 闪电持续时间（秒）
    },
    "slow": {
        "name": "时间减速",
        "last_used": 0,
        "active": False,
        "duration": 4  # 减速持续时间（秒）
    }
}

# 技能效果变量
firestorm_particles = []  # 火焰粒子
lightning_targets = []  # 闪电目标
slow_factor = 1.0  # 减速因子

# 天空元素变量
stars = []
clouds = []
star_update_counter = 0
cloud_update_counter = 0
STAR_UPDATE_INTERVAL = 300  # 每300帧更新一次星星
CLOUD_UPDATE_INTERVAL = 600  # 每600帧更新一次云朵

# 初始化天空元素
def init_sky_elements():
    global stars, clouds
    # 初始化星星
    stars = []
    for _ in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT // 2)
        size = random.randint(1, 3)
        stars.append([x, y, size])
    
    # 初始化云朵
    clouds = []
    for _ in range(5):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT // 3)
        cloud_size = random.randint(30, 60)
        clouds.append([x, y, cloud_size])

# 时钟
clock = pygame.time.Clock()
FPS = 60

# 生成怪物
def spawn_monster(is_sentence_monster=False, original_word_pair=None, spawn_x=None, spawn_y=None):
    if is_sentence_monster and original_word_pair:
        word_pair = original_word_pair
    else:
        word_pair = random.choice(WORD_LIST)
    
    # 根据单词长度计算怪物大小
    monster_size = monster_base_size + max(len(word_pair[0]), len(word_pair[1])) * 2
    
    # 如果指定了生成位置，使用指定位置；否则随机生成（屏幕边缘）
    if spawn_x is not None and spawn_y is not None:
        x, y = spawn_x, spawn_y
    else:
        # 随机生成怪物位置（屏幕边缘）
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            x = random.randint(0, WIDTH)
            y = -monster_size * 2
        elif side == "bottom":
            x = random.randint(0, WIDTH)
            y = HEIGHT + monster_size * 2
        elif side == "left":
            x = -monster_size * 2
            y = random.randint(0, HEIGHT)
        else:  # right
            x = WIDTH + monster_size * 2
            y = random.randint(0, HEIGHT)
    
    # 随机决定怪物的主语言：0=英文，1=中文
    primary_language = random.randint(0, 1)
    # 根据单词长度计算血量（每个字母需要2.5次攻击）
    max_hp = max(len(word_pair[0]), len(word_pair[1])) * 2
    max_hp = int(max_hp)  # 确保血量为整数
    
    # 如果是句子怪物，血量更高，颜色更恐怖
    if is_sentence_monster:
        max_hp = max_hp * 2  # 句子怪物血量翻倍
        monster_color = (128, 0, 128)  # 紫色，更恐怖
        monster_size = int(monster_size * 1.5)  # 句子怪物更大
    else:
        monster_color = RED
    
    # [x, y, [英文, 中文, 英文例句, 中文例句], remaining_letters, is_dead, size, show_chinese, death_time, primary_language, color, opacity, frozen, frozen_end_time, hp, max_hp, is_sentence_monster]
    monsters.append([x, y, word_pair, list(word_pair[0]), False, monster_size, False, 0, primary_language, monster_color, 255, False, 0, max_hp, max_hp, is_sentence_monster])

# 移动怪物
def move_monsters():
    global game_over
    current_time = time.time()
    for monster in monsters:
        try:
            if len(monster) >= 16 and not monster[4]:  # 如果怪物没有死亡
                # 检查冰冻状态
                if monster[11]:  # frozen
                    if current_time > monster[12]:  # frozen_end_time
                        monster[11] = False  # 解除冰冻
                        monster[9] = RED  # 恢复红色
                    else:
                        continue  # 冰冻状态不移动
                
                # 计算怪物到玩家的方向
                dx = player_x - monster[0]
                dy = player_y - monster[1]
                distance = (dx**2 + dy**2)**0.5
                if distance > 0:
                    speed = DIFFICULTY[current_difficulty]["monster_speed"] * slow_factor
                    monster[0] += (dx / distance) * speed
                    monster[1] += (dy / distance) * speed
                
                # 检查怪物是否追上玩家
                if abs(monster[0] - player_x) < PLAYER_SIZE and abs(monster[1] - player_y) < PLAYER_SIZE:
                    game_over = True
        except (IndexError, AttributeError):
            pass  # 忽略无效的怪物数据

# 获取最近的怪物
def get_closest_monster():
    if not monsters:
        return None
    closest_monster = None
    min_distance = float('inf')
    for monster in monsters:
        try:
            if len(monster) >= 16 and not monster[4]:  # 如果怪物没有死亡
                distance = ((monster[0] - player_x)**2 + (monster[1] - player_y)**2)**0.5
                # 只考虑在攻击范围内的怪物
                if distance <= ATTACK_RANGE and distance < min_distance:
                    min_distance = distance
                    closest_monster = monster
        except (IndexError, AttributeError):
            pass
    return closest_monster

# 获取攻击范围内的随机怪物
def get_random_monster_in_range():
    if not monsters:
        return None
    monsters_in_range = []
    for monster in monsters:
        try:
            if len(monster) >= 16 and not monster[4]:  # 如果怪物没有死亡
                distance = ((monster[0] - player_x)**2 + (monster[1] - player_y)**2)**0.5
                # 只考虑在攻击范围内的怪物
                if distance <= ATTACK_RANGE:
                    monsters_in_range.append(monster)
        except (IndexError, AttributeError):
            pass
    if monsters_in_range:
        return random.choice(monsters_in_range)
    return None

# 发射子弹
def shoot_bullet(target_x=None, target_y=None):
    global last_shot_time, last_tts_time, clip_bullets
    target_monster = get_random_monster_in_range()
    try:
        if target_monster and len(target_monster) >= 16 and not target_monster[4]:
            current_time = time.time()
            can_shoot = current_time - last_shot_time >= BULLET_COOLDOWN
            
            if not can_shoot:
                return  # 冷却时间未到，不发射
            
            # 显示怪物的次要语言
            target_monster[6] = True
            
            # 检查是否是句子怪物
            if len(target_monster) >= 16 and target_monster[15]:
                # 句子怪物：使用整个例句
                word_pair = target_monster[2]
                if len(word_pair) >= 4 and word_pair[2] and word_pair[3]:
                    # 使用英文例句作为子弹
                    bullet_word = word_pair[2]
                else:
                    bullet_word = word_pair[0]
            else:
                # 普通怪物：根据主语言决定子弹使用的语言
                if target_monster[8] == 0:  # 英文怪物，子弹用中文
                    bullet_word = target_monster[2][1]
                else:  # 中文怪物，子弹用英文
                    bullet_word = target_monster[2][0]
            
            # 添加到弹夹
            clip_bullets.append(bullet_word)
            if len(clip_bullets) > 10:  # 弹夹最多显示10发
                clip_bullets.pop(0)
            
            # 计算子弹方向（从玩家位置到目标位置）
            if target_x is not None and target_y is not None:
                dx = target_x - player_x
                dy = target_y - player_y
            else:
                dx = target_monster[0] - player_x
                dy = target_monster[1] - player_y
            distance = (dx**2 + dy**2)**0.5
            if distance > 0:
                bullet_vel = DIFFICULTY[current_difficulty]["bullet_vel"]
                can_use_tts = current_time - last_tts_time >= TTS_COOLDOWN
                
                # 如果TTS冷却时间到了，使用文本转语音
                if HAS_TTS and can_use_tts:
                    try:
                        # 检查是否是句子怪物
                        if len(target_monster) >= 16 and target_monster[15]:
                            # 句子怪物：播放英文例句
                            word_pair = target_monster[2]
                            if len(word_pair) >= 4 and word_pair[2]:
                                word_to_speak = word_pair[2]
                            else:
                                word_to_speak = word_pair[0]
                        else:
                            # 普通怪物：播放英文和中文
                            word_pair = target_monster[2]
                            word_to_speak = f"{word_pair[0]}, {word_pair[1]}"
                        
                        # 使用异步模式播放语音，并清除之前的语音
                        speaker.Speak(word_to_speak, 1 | 2)  # 1=异步执行, 2=清除之前的语音
                        
                        last_tts_time = current_time  # 更新TTS调用时间
                    except:
                        pass  # 如果TTS失败，忽略错误
                else:
                    # 播放子弹发射音效
                    try:
                        sound = pygame.mixer.Sound('D:\\qlib\\word_monster_game\\菜鸟图库-电浆枪射击.mp3')
                        sound.set_volume(0.1)
                        sound.play()
                    except:
                        pass  # 如果没有音效文件，忽略错误
                
                # 更新最后发射的时间
                last_shot_time = current_time
                
                bullets.append([player_x, player_y, (dx/distance)*bullet_vel, (dy/distance)*bullet_vel, None, target_monster, False, bullet_word])  # [x, y, dx, dy, letter, target_monster, is_dead, bullet_word]
    except (IndexError, AttributeError, ZeroDivisionError):
        pass

# 移动子弹
def move_bullets():
    global score
    for bullet in bullets:
        if not bullet[6]:  # 如果子弹没有死亡
            # 记录子弹的前一位置
            prev_x, prev_y = bullet[0], bullet[1]
            # 移动子弹
            bullet[0] += bullet[2] * bullet_speed
            bullet[1] += bullet[3] * bullet_speed
            
            # 检查子弹是否击中目标怪物
            target_monster = bullet[5]
            try:
                if target_monster and len(target_monster) >= 16 and not target_monster[4]:  # 如果目标怪物存在且未死亡
                    # 计算长方形怪物的碰撞区域
                    rect_width = target_monster[5] * 2
                    rect_height = target_monster[5]
                    monster_left = target_monster[0] - rect_width//2
                    monster_right = target_monster[0] + rect_width//2
                    monster_top = target_monster[1] - rect_height//2
                    monster_bottom = target_monster[1] + rect_height//2
                    
                    # 检查子弹是否在怪物的矩形范围内
                    if (monster_left < bullet[0] < monster_right) and (monster_top < bullet[1] < monster_bottom):
                        # 标记子弹为死亡
                        bullet[6] = True
                        
                        # 减少怪物血量
                        target_monster[13] -= 1  # hp
                        current_hp = target_monster[13]
                        max_hp = target_monster[14]
                        
                        # 让怪物后退（沿着子弹方向的相反方向）
                        knockback_distance = -40  # 后退距离
                        target_monster[0] -= bullet[2] * knockback_distance  # x方向后退
                        target_monster[1] -= bullet[3] * knockback_distance  # y方向后退
                        
                        # 确保怪物不会退到屏幕外
                        target_monster[0] = max(50, min(WIDTH - 50, target_monster[0]))
                        target_monster[1] = max(50, min(HEIGHT - 50, target_monster[1]))
                        
                        # 根据血量比例改变怪物颜色
                        if max_hp > 0:
                            hp_ratio = current_hp / max_hp
                        else:
                            hp_ratio = 0
                        
                        if hp_ratio > 0.7:
                            target_monster[9] = RED
                        elif hp_ratio > 0.4:
                            target_monster[9] = (255, 165, 0)  # 橙色
                        elif hp_ratio > 0.2:
                            target_monster[9] = (255, 100, 100)  # 浅红色
                        else:
                            target_monster[9] = (128, 0, 0)  # 深红色
                        
                        # 播放字母消除音效
                        try:
                            sound = pygame.mixer.Sound('D:\\qlib\\word_monster_game\\菜鸟图库-受伤"啊"音.mp3')
                            sound.set_volume(0.2)
                            sound.play()
                        except:
                            pass  # 如果没有音效文件，忽略错误
                        
                        # 触发随机技能
                        trigger_random_skill()
                        
                        # 检查怪物血量是否为0（死亡条件）
                        if current_hp <= 0:
                            # 记录怪物死亡位置
                            death_x = target_monster[0]
                            death_y = target_monster[1]
                            
                            target_monster[4] = True  # 标记怪物为死亡
                            target_monster[7] = time.time()  # 记录死亡时间
                            score += 1
                            
                            # 检查是否是句子怪物
                            if not target_monster[15]:  # 不是句子怪物
                                # 检查是否有例句
                                word_pair = target_monster[2]
                                if len(word_pair) >= 4 and word_pair[2] and word_pair[3]:  # 有例句
                                    # 在原地生成句子怪物
                                    spawn_monster(is_sentence_monster=True, original_word_pair=word_pair, spawn_x=death_x, spawn_y=death_y)
                            
                            # 播放怪物消除音效
                            try:
                                sound = pygame.mixer.Sound('D:\\qlib\\word_monster_game\\气球爆炸_爱给网_aigei_com.mp3')
                                sound.set_volume(0.025)
                                sound.play()
                            except:
                                pass  # 如果没有音效文件，忽略错误
            except (IndexError, AttributeError):
                pass  # 忽略无效的怪物数据
            
            # 检查子弹是否飞出屏幕
            if bullet[0] < 0 or bullet[0] > WIDTH or bullet[1] < 0 or bullet[1] > HEIGHT:
                bullet[6] = True

# 移除死亡的子弹
def remove_dead_bullets():
    global bullets
    try:
        bullets[:] = [bullet for bullet in bullets if not bullet[6]]
    except (IndexError, AttributeError):
        pass

# 触发随机技能
def trigger_random_skill():
    current_time = time.time()
    skill_keys = list(skills.keys())
    random.shuffle(skill_keys)
    
    for skill_key in skill_keys:
        skill = skills[skill_key]
        if current_time - skill["last_used"] >= SKILL_COOLDOWN:
            # if skill_key == "freeze":
            #     activate_freeze_skill()
            #     return True
            if skill_key == "firestorm":
                activate_firestorm_skill()
                return True
            elif skill_key == "lightning":
                activate_lightning_skill()
                return True
            elif skill_key == "slow":
                activate_slow_skill()
                return True
    return False

# 移除死亡的怪物
def remove_dead_monsters():
    global monsters
    current_time = time.time()
    # 只移除死亡时间超过1秒的怪物
    try:
        monsters[:] = [monster for monster in monsters if not monster[4] or (current_time - monster[7] < 1)]
    except (IndexError, AttributeError):
        pass

# 激活冰冻技能
def activate_freeze_skill():
    current_time = time.time()
    if current_time - skills["freeze"]["last_used"] >= SKILL_COOLDOWN:
        skills["freeze"]["last_used"] = current_time
        skills["freeze"]["active"] = True
        # 只对攻击范围内的怪物应用冰冻效果
        end_time = current_time + skills["freeze"]["duration"]
        for monster in monsters:
            try:
                if len(monster) >= 16 and not monster[4]:  # 只对活着的怪物生效
                    # 检查是否在攻击范围内
                    distance = ((monster[0] - player_x)**2 + (monster[1] - player_y)**2)**0.5
                    if distance <= ATTACK_RANGE:
                        monster[11] = True  # frozen
                        monster[12] = end_time  # frozen_end_time
                        monster[9] = (0, 191, 255)  # 变为冰蓝色
            except (IndexError, AttributeError):
                pass
        return True
    return False

# 激活火焰风暴技能
def activate_firestorm_skill():
    global firestorm_particles
    current_time = time.time()
    if current_time - skills["firestorm"]["last_used"] >= SKILL_COOLDOWN:
        skills["firestorm"]["last_used"] = current_time
        skills["firestorm"]["active"] = True
        
        # 在攻击范围内生成火焰粒子
        firestorm_particles = []
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, ATTACK_RANGE)
            firestorm_particles.append([
                player_x + radius * math.cos(angle),
                player_y + radius * math.sin(angle),
                random.randint(-3, 3),  # dx
                random.randint(-3, 3),  # dy
                random.randint(20, 40),  # size
                random.randint(100, 255),  # red
                random.randint(50, 150),  # green
                0,  # blue
                random.randint(150, 255)  # alpha
            ])
        
        # 只对攻击范围内的怪物造成伤害
        for monster in monsters:
            try:
                if len(monster) >= 16 and not monster[4]:
                    # 检查是否在攻击范围内
                    distance = ((monster[0] - player_x)**2 + (monster[1] - player_y)**2)**0.5
                    if distance <= ATTACK_RANGE:
                        monster[13] = max(0, monster[13] - 5)  # 减少5点血量
                        if monster[13] <= 0:
                            monster[4] = True
                            monster[7] = current_time
                            global score
                            score += 1
            except (IndexError, AttributeError):
                pass
        
        return True
    return False

# 激活闪电链技能
def activate_lightning_skill():
    global lightning_targets
    current_time = time.time()
    if current_time - skills["lightning"]["last_used"] >= SKILL_COOLDOWN:
        skills["lightning"]["last_used"] = current_time
        skills["lightning"]["active"] = True
        
        # 选择攻击范围内最近的3个怪物作为闪电目标
        alive_monsters = []
        for m in monsters:
            try:
                if len(m) >= 16 and not m[4]:
                    # 检查是否在攻击范围内
                    distance = ((m[0] - player_x)**2 + (m[1] - player_y)**2)**0.5
                    if distance <= ATTACK_RANGE:
                        alive_monsters.append(m)
            except (IndexError, AttributeError):
                pass
        
        if alive_monsters:
            # 按距离排序
            alive_monsters.sort(key=lambda m: (m[0] - player_x)**2 + (m[1] - player_y)**2)
            # 选择最近的3个
            lightning_targets = alive_monsters[:3]
            
            # 对目标造成大量伤害
            for monster in lightning_targets:
                try:
                    if len(monster) >= 16:
                        monster[13] = max(0, monster[13] - 8)  # 减少8点血量
                        if monster[13] <= 0:
                            monster[4] = True
                            monster[7] = current_time
                            global score
                            score += 1
                except (IndexError, AttributeError):
                    pass
        
        return True
    return False

# 激活时间减速技能
def activate_slow_skill():
    global slow_factor
    current_time = time.time()
    if current_time - skills["slow"]["last_used"] >= SKILL_COOLDOWN:
        skills["slow"]["last_used"] = current_time
        skills["slow"]["active"] = True
        slow_factor = 0.3  # 减速到30%
        return True
    return False

# 检查技能状态
def check_skills():
    global firestorm_particles, lightning_targets, slow_factor
    current_time = time.time()
    
    # 检查冰冻技能
    if skills["freeze"]["active"]:
        # 检查是否有怪物还在冰冻状态
        any_frozen = False
        for monster in monsters:
            try:
                if len(monster) >= 16 and not monster[4] and monster[11]:
                    any_frozen = True
                    break
            except (IndexError, AttributeError):
                pass
        if not any_frozen:
            skills["freeze"]["active"] = False
    
    # 检查火焰风暴技能
    if skills["firestorm"]["active"]:
        if current_time - skills["firestorm"]["last_used"] >= skills["firestorm"]["duration"]:
            skills["firestorm"]["active"] = False
            firestorm_particles = []
    
    # 检查闪电技能
    if skills["lightning"]["active"]:
        if current_time - skills["lightning"]["last_used"] >= skills["lightning"]["duration"]:
            skills["lightning"]["active"] = False
            lightning_targets = []
    
    # 检查减速技能
    if skills["slow"]["active"]:
        if current_time - skills["slow"]["last_used"] >= skills["slow"]["duration"]:
            skills["slow"]["active"] = False
            slow_factor = 1.0



# 绘制游戏元素
def draw_game():
    # 绘制渐变背景
    for y in range(HEIGHT):
        r = 240 + (y * 15) // HEIGHT
        g = 240 + (y * 15) // HEIGHT
        b = 255
        pygame.draw.line(WIN, (r, g, b), (0, y), (WIDTH, y))
    
    # 绘制星星
    for star in stars:
        x, y, size = star
        pygame.draw.circle(WIN, (255, 255, 220), (x, y), size)
    
    # 绘制云朵
    for cloud in clouds:
        x, y, cloud_size = cloud
        # 绘制云朵
        pygame.draw.circle(WIN, (255, 255, 255), (x, y), cloud_size // 2)
        pygame.draw.circle(WIN, (255, 255, 255), (x + cloud_size // 3, y), cloud_size // 2)
        pygame.draw.circle(WIN, (255, 255, 255), (x - cloud_size // 3, y), cloud_size // 2)
        pygame.draw.circle(WIN, (255, 255, 255), (x, y - cloud_size // 3), cloud_size // 2)
    
    # 绘制火焰粒子
    # if skills["firestorm"]["active"]:
    #     for particle in firestorm_particles:
    #         try:
    #             x, y, dx, dy, size, r, g, b, a = particle
    #             # 创建带透明度的表面
    #             particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    #             pygame.draw.circle(particle_surf, (r, g, b, a), (size, size), size)
    #             WIN.blit(particle_surf, (int(x) - size, int(y) - size))
    #             
    #             # 更新粒子位置
    #             particle[0] += dx
    #             particle[1] += dy
    #             particle[7] = max(0, particle[7] - 5)  # 减少透明度
    #             particle[4] = max(5, particle[4] - 0.5)  # 减小尺寸
    #         except (IndexError, AttributeError):
    #             pass
    
    # 绘制闪电效果
    # if skills["lightning"]["active"] and lightning_targets:
    #     for monster in lightning_targets:
    #         try:
    #             if monster and len(monster) >= 16 and not monster[4]:
    #                 # 从玩家到怪物绘制闪电
    #                 start_pos = (int(player_x), int(player_y))
    #                 end_pos = (int(monster[0]), int(monster[1]))
    #                 
    #                 # 绘制多条闪电线
    #                 for j in range(3):
    #                     offset_x = random.randint(-10, 10)
    #                     offset_y = random.randint(-10, 10)
    #                     mid_pos = ((start_pos[0] + end_pos[0]) // 2 + offset_x, 
    #                               (start_pos[1] + end_pos[1]) // 2 + offset_y)
    #                     pygame.draw.line(WIN, (255, 255, 0), start_pos, mid_pos, 3)
    #                     pygame.draw.line(WIN, (255, 255, 0), mid_pos, end_pos, 3)
    #                 
    #                 # 绘制发光效果
    #                 pygame.draw.circle(WIN, (255, 255, 200), end_pos, 20, 2)
    #         except (IndexError, AttributeError):
    #             pass  # 忽略已死亡的怪物
    
    # 绘制玩家
    # 玩家身体（圆形）
    pygame.draw.circle(WIN, BLUE, (int(player_x), int(player_y)), PLAYER_SIZE//2)
    
    # 玩家眼睛
    eye_size = PLAYER_SIZE // 6
    eye_offset = PLAYER_SIZE // 4
    # 白色眼白
    pygame.draw.circle(WIN, WHITE, (int(player_x) - eye_offset, int(player_y) - PLAYER_SIZE//6), eye_size)
    pygame.draw.circle(WIN, WHITE, (int(player_x) + eye_offset, int(player_y) - PLAYER_SIZE//6), eye_size)
    # 黑色瞳孔
    pupil_size = eye_size // 2
    pygame.draw.circle(WIN, BLACK, (int(player_x) - eye_offset, int(player_y) - PLAYER_SIZE//6), pupil_size)
    pygame.draw.circle(WIN, BLACK, (int(player_x) + eye_offset, int(player_y) - PLAYER_SIZE//6), pupil_size)
    
    # 玩家嘴巴（微笑）
    mouth_width = PLAYER_SIZE // 2
    mouth_height = PLAYER_SIZE // 6
    pygame.draw.arc(WIN, BLACK, (
        int(player_x) - mouth_width//2, 
        int(player_y) + PLAYER_SIZE//6, 
        mouth_width, 
        mouth_height
    ), 0, 3.14, 2)
    
    # 玩家
    limb_size = PLAYER_SIZE // 5
    # 左
    pygame.draw.line(WIN, BLUE, (int(player_x) - PLAYER_SIZE//2, int(player_y)), 
                   (int(player_x) - PLAYER_SIZE//2 - limb_size*2, int(player_y) - limb_size), limb_size)
    # 右
    pygame.draw.line(WIN, BLUE, (int(player_x) + PLAYER_SIZE//2, int(player_y)), 
                   (int(player_x) + PLAYER_SIZE//2 + limb_size*2, int(player_y) - limb_size), limb_size)
    # 左
    pygame.draw.line(WIN, BLUE, (int(player_x) - PLAYER_SIZE//4, int(player_y) + PLAYER_SIZE//2), 
                   (int(player_x) - PLAYER_SIZE//4 - limb_size, int(player_y) + PLAYER_SIZE//2 + limb_size*2), limb_size)
    # 右
    pygame.draw.line(WIN, BLUE, (int(player_x) + PLAYER_SIZE//4, int(player_y) + PLAYER_SIZE//2), 
                   (int(player_x) + PLAYER_SIZE//4 + limb_size, int(player_y) + PLAYER_SIZE//2 + limb_size*2), limb_size)
    
    # 绘制攻击范围圈
    pygame.draw.circle(WIN, (0, 200, 255), (int(player_x), int(player_y)), ATTACK_RANGE, 2)
    
    # 绘制即将发射的子弹内容
    if next_bullet_word:
        next_bullet_text = FONT.render(next_bullet_word, True, BLACK)
        next_bullet_rect = next_bullet_text.get_rect(center=(int(player_x), int(player_y) - PLAYER_SIZE - 20))
        WIN.blit(next_bullet_text, next_bullet_rect)
    
    # 绘制怪物
    for monster in monsters:
        try:
            if not monster[4]:
                # 计算长方形怪物的尺寸
                rect_width = monster[5] * 2
                rect_height = monster[5]
                
                # 获取怪物颜色和透明度
                color = monster[9]
                opacity = monster[10]
                
                # 创建更大的表面以容纳旋转后的怪物
                max_dim = max(rect_width, rect_height) * 2
                monster_surf = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)
                center_x, center_y = max_dim // 2, max_dim // 2
                
                # 绘制怪物身体（长方形）
                pygame.draw.rect(monster_surf, (*color, opacity), 
                               (center_x - rect_width//2, center_y - rect_height//2, rect_width, rect_height))
                
                # 眼睛
                eye_size = monster[5] // 5
                pygame.draw.circle(monster_surf, WHITE, (center_x - rect_width//4, center_y - rect_height//4), eye_size)
                pygame.draw.circle(monster_surf, WHITE, (center_x + rect_width//4, center_y - rect_height//4), eye_size)
                pygame.draw.circle(monster_surf, BLACK, (center_x - rect_width//4, center_y - rect_height//4), eye_size // 2)
                pygame.draw.circle(monster_surf, BLACK, (center_x + rect_width//4, center_y - rect_height//4), eye_size // 2)
                
                # 嘴巴
                pygame.draw.arc(monster_surf, BLACK, (
                    center_x - rect_width//3, 
                    center_y + rect_height//6, 
                    rect_width//1.5, 
                    rect_height//2
                ), 0, 3.14, 2)
                
                # 角
                pygame.draw.polygon(monster_surf, (255, 165, 0), [
                    (center_x, center_y - rect_height//2),
                    (center_x - rect_width//4, center_y),
                    (center_x + rect_width//4, center_y)
                ])
                
                # 四肢
                limb_size = monster[5] // 3
                # 左上肢
                pygame.draw.line(monster_surf, color, (center_x - rect_width//2, center_y - rect_height//4), 
                               (center_x - rect_width//2 - limb_size, center_y - rect_height//4 - limb_size), limb_size)
                # 右上肢
                pygame.draw.line(monster_surf, color, (center_x + rect_width//2, center_y - rect_height//4), 
                               (center_x + rect_width//2 + limb_size, center_y - rect_height//4 - limb_size), limb_size)
                # 左下肢
                pygame.draw.line(monster_surf, color, (center_x - rect_width//4, center_y + rect_height//2), 
                               (center_x - rect_width//4 - limb_size, center_y + rect_height//2 + limb_size), limb_size)
                # 右下肢
                pygame.draw.line(monster_surf, color, (center_x + rect_width//4, center_y + rect_height//2), 
                               (center_x + rect_width//4 + limb_size, center_y + rect_height//2 + limb_size), limb_size)
                
                # 绘制到窗口
                rect = monster_surf.get_rect(center=(int(monster[0]), int(monster[1])))
                WIN.blit(monster_surf, rect)
                
                # 绘制血条
                if len(monster) >= 16:
                    current_hp = monster[13]
                    max_hp = monster[14]
                    hp_bar_width = rect_width
                    hp_bar_height = 6
                    hp_bar_x = int(monster[0]) - hp_bar_width // 2
                    hp_bar_y = int(monster[1]) - rect_height - 20
                    
                    # 血条背景（灰色）
                    pygame.draw.rect(WIN, (128, 128, 128), (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
                    
                    # 血条前景（根据血量比例变色）
                    if max_hp > 0:
                        hp_ratio = current_hp / max_hp
                    else:
                        hp_ratio = 0
                    
                    if hp_ratio > 0.7:
                        hp_color = GREEN
                    elif hp_ratio > 0.4:
                        hp_color = (255, 255, 0)  # 黄色
                    elif hp_ratio > 0.2:
                        hp_color = (255, 165, 0)  # 橙色
                    else:
                        hp_color = RED
                    
                    # 绘制当前血量
                    pygame.draw.rect(WIN, hp_color, (hp_bar_x, hp_bar_y, int(hp_bar_width * hp_ratio), hp_bar_height))
                    
                    # 血条边框
                    pygame.draw.rect(WIN, BLACK, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 1)
                
                # 根据主语言绘制对应单词
                # 检查是否是句子怪物
                if len(monster) >= 16 and monster[15]:  # 句子怪物
                    # 显示例句
                    word_pair = monster[2]
                    if len(word_pair) >= 4 and word_pair[2] and word_pair[3]:
                        # 英文例句（上方）
                        en_sentence = word_pair[2]
                        en_text = SMALL_FONT.render(en_sentence, True, BLACK)
                        en_rect = en_text.get_rect(center=(int(monster[0]), int(monster[1]) - rect_height - 20))
                        WIN.blit(en_text, en_rect)
                        
                        # 中文例句（下方）
                        cn_sentence = word_pair[3]
                        cn_text = SMALL_FONT.render(cn_sentence, True, BLACK)
                        cn_rect = cn_text.get_rect(center=(int(monster[0]), int(monster[1]) + rect_height + 20))
                        WIN.blit(cn_text, cn_rect)
                elif monster[8] == 0:  # 英文怪物
                    # 绘制英文单词（在怪物上方）
                    remaining_word = ''.join(monster[3])
                    word_text = FONT.render(remaining_word, True, BLACK)
                    text_rect = word_text.get_rect(center=(int(monster[0]), int(monster[1]) - rect_height))
                    WIN.blit(word_text, text_rect)
                    # 绘制中文单词（在怪物下方）- 只在show_chinese为True时显示
                    if monster[6]:
                        chinese_text = SMALL_FONT.render(monster[2][1], True, BLACK)
                        chinese_rect = chinese_text.get_rect(center=(int(monster[0]), int(monster[1]) + rect_height))
                        WIN.blit(chinese_text, chinese_rect)
                else:  # 中文怪物
                    # 绘制中文单词（在怪物上方）
                    chinese_word = monster[2][1]
                    chinese_text = FONT.render(chinese_word, True, BLACK)
                    chinese_rect = chinese_text.get_rect(center=(int(monster[0]), int(monster[1]) - rect_height))
                    WIN.blit(chinese_text, chinese_rect)
                    # 绘制英文单词（在怪物下方）- 只在show_chinese为True时显示
                    if monster[6]:
                        english_text = SMALL_FONT.render(monster[2][0], True, BLACK)
                        english_rect = english_text.get_rect(center=(int(monster[0]), int(monster[1]) + rect_height))
                        WIN.blit(english_text, english_rect)
        except (IndexError, AttributeError):
            pass  # 忽略无效的怪物数据
    # 绘制死亡的怪物 - 只显示中文
    for monster in monsters:
        try:
            if len(monster) > 4 and monster[4]:
                chinese_text = FONT.render(monster[2][1], True, BLACK)
                chinese_rect = chinese_text.get_rect(center=(int(monster[0]), int(monster[1])))
                WIN.blit(chinese_text, chinese_rect)
        except (IndexError, AttributeError):
            pass
    
    # 绘制子弹
    for bullet in bullets:
        try:
            if len(bullet) > 7 and not bullet[6]:
                # 绘制子弹（增强可见性）
                # 外发光效果
                pygame.draw.circle(WIN, YELLOW, (int(bullet[0]), int(bullet[1])), 8)
                # 主子弹
                pygame.draw.circle(WIN, (255, 165, 0), (int(bullet[0]), int(bullet[1])), 5)
                # 绘制子弹上的完整单词（更大更明显）
                bullet_text = FONT.render(bullet[7], True, BLACK)
                bullet_rect = bullet_text.get_rect(center=(int(bullet[0]), int(bullet[1]) - 15))
                WIN.blit(bullet_text, bullet_rect)
        except (IndexError, AttributeError):
            pass
    
    # 绘制分数
    # 计算存活时间
    if not game_over:
        survival_time = int(time.time() - start_time)
    else:
        survival_time = int(time.time() - start_time)
    
    # 绘制击杀数
    score_text = FONT.render(f"击杀数: {score}", True, BLACK)
    WIN.blit(score_text, (20, 20))
    
    # 绘制存活时间
    survival_text = FONT.render(f"存活时间: {survival_time}秒", True, BLACK)
    WIN.blit(survival_text, (20, 50))
    
    # 绘制游戏结束画面
    if game_over:
        over_text = FONT.render("游戏结束!", True, RED)
        over_rect = over_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        WIN.blit(over_text, over_rect)
        
        score_text = FONT.render(f"最终击杀数: {score}", True, BLACK)
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        WIN.blit(score_text, score_rect)
        
        survival_text = FONT.render(f"存活时间: {survival_time}秒", True, BLACK)
        survival_rect = survival_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
        WIN.blit(survival_text, survival_rect)
        
        restart_text = FONT.render("按R键重新开始", True, BLUE)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 150))
        WIN.blit(restart_text, restart_rect)
    
    # 绘制游戏说明
    instruction_text1 = SMALL_FONT.render("WASD移动玩家，左键向点击位置发射子弹", True, BLACK)
    WIN.blit(instruction_text1, (WIDTH - 450, 20))
    instruction_text2 = SMALL_FONT.render("击中后减少怪物血量，血量为0时怪物消灭", True, BLACK)
    WIN.blit(instruction_text2, (WIDTH - 450, 40))
    instruction_text3 = SMALL_FONT.render("子弹击中怪物时随机触发技能", True, BLACK)
    WIN.blit(instruction_text3, (WIDTH - 450, 60))
    instruction_text4 = SMALL_FONT.render("技能: 冰冻/火焰风暴/闪电链/时间减速", True, BLACK)
    WIN.blit(instruction_text4, (WIDTH - 450, 80))
    instruction_text5 = SMALL_FONT.render("按F11或f键切换全屏", True, BLACK)
    WIN.blit(instruction_text5, (WIDTH - 450, 100))
    # 绘制难度设置
    difficulty_text = SMALL_FONT.render(f"难度: {current_difficulty}", True, BLACK)
    WIN.blit(difficulty_text, (20, 80))
    # 绘制难度切换提示
    difficulty_switch_text = SMALL_FONT.render("按1(简单), 2(中等), 3(困难)切换难度", True, BLACK)
    WIN.blit(difficulty_switch_text, (20, 110))
    
    # 绘制技能状态
    current_time = time.time()
    skill_y = 140
    for skill_key, skill in skills.items():
        # 计算冷却时间
        cooldown_remaining = max(0, SKILL_COOLDOWN - (current_time - skill["last_used"]))
        if cooldown_remaining > 0:
            status_text = f"{skill['name']}: 冷却中 {cooldown_remaining:.1f}s"
            color = (128, 128, 128)  # 灰色
        elif skill["active"]:
            status_text = f"{skill['name']}: 激活中"
            color = GREEN
        else:
            status_text = f"{skill['name']}: 就绪"
            color = BLUE
        skill_text = SMALL_FONT.render(status_text, True, color)
        WIN.blit(skill_text, (20, skill_y))
        skill_y += 25  # 减小间距以容纳更多技能
    
    # 绘制弹夹（在右侧）
    clip_x = WIDTH - 200
    clip_y = HEIGHT - 300
    clip_width = 180
    clip_height = 280
    
    # 绘制弹夹背景
    pygame.draw.rect(WIN, (200, 200, 200), (clip_x, clip_y, clip_width, clip_height))
    pygame.draw.rect(WIN, BLACK, (clip_x, clip_y, clip_width, clip_height), 2)
    
    # 绘制弹夹标题
    clip_title = FONT.render("弹夹", True, BLACK)
    clip_title_rect = clip_title.get_rect(center=(clip_x + clip_width // 2, clip_y + 25))
    WIN.blit(clip_title, clip_title_rect)
    
    # 绘制弹夹中的子弹
    bullet_start_y = clip_y + 50
    for i, bullet_content in enumerate(clip_bullets):
        bullet_y = bullet_start_y + i * 25
        if bullet_y < clip_y + clip_height - 20:
            # 绘制子弹背景
            pygame.draw.rect(WIN, (255, 255, 255), (clip_x + 10, bullet_y, clip_width - 20, 20))
            pygame.draw.rect(WIN, BLACK, (clip_x + 10, bullet_y, clip_width - 20, 20), 1)
            
            # 绘制子弹内容
            bullet_text = SMALL_FONT.render(bullet_content, True, BLACK)
            bullet_rect = bullet_text.get_rect(center=(clip_x + clip_width // 2, bullet_y + 10))
            WIN.blit(bullet_text, bullet_rect)
    
    pygame.display.update()

# 重置游戏
def reset_game():
    global player_x, player_y, monsters, bullets, score, game_over, frame_count, start_time, firestorm_particles, lightning_targets, slow_factor, last_tts_time
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    monsters = []
    bullets = []
    score = 0
    game_over = False
    frame_count = 0  # 重置帧计数器
    start_time = time.time()  # 重置游戏开始时间
    firestorm_particles = []
    lightning_targets = []
    slow_factor = 1.0
    last_tts_time = 0  # 重置TTS时间
    
    # 重置技能状态
    for skill in skills.values():
        skill["last_used"] = 0
        skill["active"] = False
    
    init_sky_elements()

# 切换全屏模式
def toggle_fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        pygame.display.set_mode((WIDTH, HEIGHT))

# 主游戏循环
def main():
    global player_x, player_y, monsters, score, game_over, current_difficulty, frame_count, start_time, star_update_counter, cloud_update_counter, firestorm_particles, lightning_targets, slow_factor, last_tts_time
    frame_count = 0
    start_time = time.time()  # 记录游戏开始时间
    firestorm_particles = []
    lightning_targets = []
    slow_factor = 1.0
    last_tts_time = 0
    init_sky_elements()
    
    while True:
        clock.tick(FPS)
        frame_count += 1
        
        # 缓慢更新天空元素
        star_update_counter += 1
        cloud_update_counter += 1
        
        # 每间隔一段时间更新星星
        if star_update_counter >= STAR_UPDATE_INTERVAL:
            star_update_counter = 0
            # 随机更新一些星星的位置
            for i in range(5):  # 每次只更新5颗星星
                if stars:
                    index = random.randint(0, len(stars) - 1)
                    stars[index] = [random.randint(0, WIDTH), random.randint(0, HEIGHT // 2), random.randint(1, 3)]
        
        # 每间隔一段时间更新云朵
        if cloud_update_counter >= CLOUD_UPDATE_INTERVAL:
            cloud_update_counter = 0
            # 随机更新一些云朵的位置
            for i in range(2):  # 每次只更新2朵云
                if clouds:
                    index = random.randint(0, len(clouds) - 1)
                    clouds[index] = [random.randint(0, WIDTH), random.randint(0, HEIGHT // 3), random.randint(30, 60)]
        
        # 生成怪物
        if len(monsters) < 3 and frame_count % DIFFICULTY[current_difficulty]["spawn_rate"] == 0 and not game_over:
            spawn_monster()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        reset_game()
                else:
                    if event.key == pygame.K_1:
                        current_difficulty = "easy"
                    elif event.key == pygame.K_2:
                        current_difficulty = "medium"
                    elif event.key == pygame.K_3:
                        current_difficulty = "hard"
                    elif event.key == pygame.K_F11 or event.key == pygame.K_f:
                        toggle_fullscreen()
            # 鼠标事件
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    if event.button == 1:  # 左键点击发射子弹
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        shoot_bullet(mouse_x, mouse_y)
        
        # WASD移动玩家
        if not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]:
                if keys[pygame.K_w]:
                    player_y = max(PLAYER_SIZE//2, player_y - PLAYER_SPEED)
                if keys[pygame.K_s]:
                    player_y = min(HEIGHT - PLAYER_SIZE//2, player_y + PLAYER_SPEED)
                if keys[pygame.K_a]:
                    player_x = max(PLAYER_SIZE//2, player_x - PLAYER_SPEED)
                if keys[pygame.K_d]:
                    player_x = min(WIDTH - PLAYER_SIZE//2, player_x + PLAYER_SPEED)
        
        # 更新即将发射的子弹内容（最多每2秒更新一次）
        if not game_over:
            global next_bullet_word, last_bullet_word_update
            current_time = time.time()
            if current_time - last_bullet_word_update >= BULLET_WORD_UPDATE_INTERVAL:
                target_monster = get_random_monster_in_range()
                if target_monster and len(target_monster) >= 16 and not target_monster[4]:
                    if len(target_monster) >= 16 and target_monster[15]:
                        word_pair = target_monster[2]
                        if len(word_pair) >= 4 and word_pair[2] and word_pair[3]:
                            next_bullet_word = word_pair[2]
                        else:
                            next_bullet_word = word_pair[0]
                    else:
                        if target_monster[8] == 0:
                            next_bullet_word = target_monster[2][1]
                        else:
                            next_bullet_word = target_monster[2][0]
                else:
                    next_bullet_word = ""
                last_bullet_word_update = current_time
        
        # 移动怪物
        move_monsters()
        
        # 移动子弹
        move_bullets()
        
        # 检查技能状态
        check_skills()
        
        # 移除死亡的怪物
        remove_dead_monsters()
        
        # 移除死亡的子弹
        remove_dead_bullets()
        
        # 绘制游戏
        draw_game()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("游戏被用户中断")
    finally:
        pygame.quit()
        sys.exit()