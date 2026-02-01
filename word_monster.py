import pygame
import random
import sys
import time

# 尝试导入文本转语音模块
try:
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    # 设置语速（-10到10，默认为0）
    speaker.Rate = 5  # 加快语速
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
        "bullet_vel": 1,  # 子弹速度与怪物速度一致
        "spawn_rate": 200
    },
    "medium": {
        "monster_speed": 1.5,
        "bullet_vel": 1.5,  # 子弹速度与怪物速度一致
        "spawn_rate": 150
    },
    "hard": {
        "monster_speed": 2,
        "bullet_vel": 2,  # 子弹速度与怪物速度一致
        "spawn_rate": 100
    }
}
current_difficulty = "easy"  # 默认难度

# 字体设置
FONT = pygame.font.SysFont('SimHei', 30)
SMALL_FONT = pygame.font.SysFont('SimHei', 20)

# 玩家设置
PLAYER_SIZE = 40
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 8

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
                    # 提取英文单词（第一个空格前的内容）
                    parts = line.split(' ')
                    if parts:
                        english_word = parts[0]
                        # 提取中文释义（包含n. v. adj.等词性后的内容）
                        chinese_part = ' '.join(parts[1:])
                        # 过滤掉词性标记和乱码，只保留中文
                        chinese_word = ''
                        for char in chinese_part:
                            if '\u4e00' <= char <= '\u9fff':
                                chinese_word += char
                        if english_word and chinese_word:
                            WORD_LIST.append([english_word, chinese_word])
        # 如果解析失败，使用默认单词列表
        if not WORD_LIST:
            WORD_LIST = [["apple", "苹果"], ["banana", "香蕉"], ["cherry", "樱桃"], ["orange", "橙子"], ["grape", "葡萄"], 
                         ["watermelon", "西瓜"], ["strawberry", "草莓"], ["pineapple", "菠萝"], ["mango", "芒果"], ["peach", "桃子"],
                         ["computer", "电脑"], ["keyboard", "键盘"], ["mouse", "鼠标"], ["monitor", "显示器"], ["printer", "打印机"], 
                         ["speaker", "音箱"], ["headphone", "耳机"], ["laptop", "笔记本"], ["tablet", "平板"], ["phone", "手机"],
                         ["python", "蟒蛇"], ["java", "咖啡"], ["c++", "C加加"], ["javascript", "脚本"], ["html", "超文本"], 
                         ["css", "样式表"], ["ruby", "红宝石"], ["php", "超文本"], ["swift", "迅捷"], ["kotlin", "科特林"]]
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
last_bullet_word = ""  # 上一次发射的子弹内容
last_shot_time = 0  # 上一次发射的时间

# 时钟
clock = pygame.time.Clock()
FPS = 60

# 生成怪物
def spawn_monster():
    word_pair = random.choice(WORD_LIST)
    # 根据单词长度计算怪物大小
    monster_size = monster_base_size + max(len(word_pair[0]), len(word_pair[1])) * 2
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
    # [x, y, [英文, 中文], remaining_letters, is_dead, size, show_chinese, death_time, primary_language, color, opacity]
    monsters.append([x, y, word_pair, list(word_pair[0]), False, monster_size, False, 0, primary_language, RED, 255])

# 移动怪物
def move_monsters():
    global game_over
    for monster in monsters:
        if not monster[4]:  # 如果怪物没有死亡
            # 计算怪物到玩家的方向
            dx = player_x - monster[0]
            dy = player_y - monster[1]
            distance = (dx**2 + dy**2)**0.5
            if distance > 0:
                speed = DIFFICULTY[current_difficulty]["monster_speed"]
                monster[0] += (dx / distance) * speed
                monster[1] += (dy / distance) * speed
            
            # 检查怪物是否追上玩家
            if abs(monster[0] - player_x) < PLAYER_SIZE and abs(monster[1] - player_y) < PLAYER_SIZE:
                game_over = True

# 获取最近的怪物
def get_closest_monster():
    if not monsters:
        return None
    closest_monster = None
    min_distance = float('inf')
    for monster in monsters:
        if not monster[4]:  # 如果怪物没有死亡
            distance = ((monster[0] - player_x)**2 + (monster[1] - player_y)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                closest_monster = monster
    return closest_monster

# 发射子弹
def shoot_bullet():
    global last_shot_time, last_bullet_word
    closest_monster = get_closest_monster()
    if closest_monster and not closest_monster[4]:
        # 显示怪物的次要语言
        closest_monster[6] = True
        # 根据怪物的主语言决定子弹使用的语言
        if closest_monster[8] == 0:  # 英文怪物，子弹用中文
            bullet_word = closest_monster[2][1]
        else:  # 中文怪物，子弹用英文
            bullet_word = closest_monster[2][0]
        # 计算子弹方向（从玩家位置到怪物位置）
        dx = closest_monster[0] - player_x
        dy = closest_monster[1] - player_y
        distance = (dx**2 + dy**2)**0.5
        if distance > 0:
            bullet_vel = DIFFICULTY[current_difficulty]["bullet_vel"]
            # 检查是否连续发射相同的子弹
            current_time = time.time()
            is_rapid_fire = current_time - last_shot_time < 0.3  # 0.3秒内视为快速连续发射
            
            # 如果是快速连续发射且子弹内容相同，使用文本转语音
            if is_rapid_fire and bullet_word == last_bullet_word and HAS_TTS:
                try:
                    # 使用异步模式播放语音，避免卡顿
                    speaker.Speak(bullet_word, 1)  # 1 表示异步执行
                except:
                    pass  # 如果TTS失败，忽略错误
            else:
                # 播放子弹发射音效
                try:
                    sound = pygame.mixer.Sound('D:\\菜鸟图库-电浆枪射击.mp3')
                    sound.set_volume(0.1)
                    sound.play()
                except:
                    pass  # 如果没有音效文件，忽略错误
            
            # 更新最后发射的子弹内容和时间
            last_bullet_word = bullet_word
            last_shot_time = current_time
            
            bullets.append([player_x, player_y, (dx/distance)*bullet_vel, (dy/distance)*bullet_vel, None, closest_monster, False, bullet_word])  # [x, y, dx, dy, letter, target_monster, is_dead, bullet_word]

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
            if target_monster and not target_monster[4]:  # 如果目标怪物存在且未死亡
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
                    
                    # 改变怪物颜色并变淡
                    target_monster[9] = (255, 165, 0)  # 变为橙色
                    target_monster[10] = max(50, target_monster[10] - 50)  # 降低透明度
                    
                    # 播放字母消除音效
                    try:
                        sound = pygame.mixer.Sound('D:\菜鸟图库-受伤“啊”音.mp3')
                        sound.set_volume(0.2)
                        sound.play()
                    except:
                        pass  # 如果没有音效文件，忽略错误
                    
                    # 检查怪物是否透明度足够低（死亡条件）
                    if target_monster[10] <= 50:
                        target_monster[4] = True  # 标记怪物为死亡
                        target_monster[7] = time.time()  # 记录死亡时间
                        score += 1
                        # 播放怪物消除音效
                        try:
                            sound = pygame.mixer.Sound('D:\气球爆炸_爱给网_aigei_com.mp3')
                            sound.set_volume(0.3)
                            sound.play()
                        except:
                            pass  # 如果没有音效文件，忽略错误
            
            # 检查子弹是否飞出屏幕
            if bullet[0] < 0 or bullet[0] > WIDTH or bullet[1] < 0 or bullet[1] > HEIGHT:
                bullet[6] = True

# 移除死亡的子弹
def remove_dead_bullets():
    global bullets
    bullets = [bullet for bullet in bullets if not bullet[6]]

# 移除死亡的怪物
def remove_dead_monsters():
    global monsters
    current_time = time.time()
    # 只移除死亡时间超过1秒的怪物
    monsters = [monster for monster in monsters if not monster[4] or (current_time - monster[7] < 1)]



# 绘制游戏元素
def draw_game():
    WIN.fill(WHITE)
    
    # 绘制玩家
    pygame.draw.rect(WIN, BLUE, (player_x - PLAYER_SIZE//2, player_y - PLAYER_SIZE//2, PLAYER_SIZE, PLAYER_SIZE))
    
    # 绘制怪物
    for monster in monsters:
        if not monster[4]:
            # 计算长方形怪物的尺寸
            rect_width = monster[5] * 2
            rect_height = monster[5]
            
            # 获取怪物颜色和透明度
            color = monster[9]
            opacity = monster[10]
            
            # 创建半透明表面
            surf = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
            # 绘制怪物身体（长方形）
            pygame.draw.rect(surf, (*color, opacity), (0, 0, rect_width, rect_height))
            # 绘制到窗口
            WIN.blit(surf, (int(monster[0]) - rect_width//2, int(monster[1]) - rect_height//2))
            
            # 眼睛
            eye_size = monster[5] // 5
            pygame.draw.circle(WIN, WHITE, (int(monster[0]) - rect_width//4, int(monster[1]) - rect_height//4), eye_size)
            pygame.draw.circle(WIN, WHITE, (int(monster[0]) + rect_width//4, int(monster[1]) - rect_height//4), eye_size)
            pygame.draw.circle(WIN, BLACK, (int(monster[0]) - rect_width//4, int(monster[1]) - rect_height//4), eye_size // 2)
            pygame.draw.circle(WIN, BLACK, (int(monster[0]) + rect_width//4, int(monster[1]) - rect_height//4), eye_size // 2)
            # 嘴巴
            pygame.draw.arc(WIN, BLACK, (
                int(monster[0]) - rect_width//3, 
                int(monster[1]) + rect_height//6, 
                rect_width//1.5, 
                rect_height//2
            ), 0, 3.14, 2)
            # 角
            pygame.draw.polygon(WIN, (255, 165, 0), [
                (int(monster[0]), int(monster[1]) - rect_height//2),
                (int(monster[0]) - rect_width//4, int(monster[1])),
                (int(monster[0]) + rect_width//4, int(monster[1]))
            ])
            # 四肢
            limb_size = monster[5] // 3
            # 左上肢
            pygame.draw.line(WIN, color, (int(monster[0]) - rect_width//2, int(monster[1]) - rect_height//4), 
                           (int(monster[0]) - rect_width//2 - limb_size, int(monster[1]) - rect_height//4 - limb_size), limb_size)
            # 右上肢
            pygame.draw.line(WIN, color, (int(monster[0]) + rect_width//2, int(monster[1]) - rect_height//4), 
                           (int(monster[0]) + rect_width//2 + limb_size, int(monster[1]) - rect_height//4 - limb_size), limb_size)
            # 左下肢
            pygame.draw.line(WIN, color, (int(monster[0]) - rect_width//4, int(monster[1]) + rect_height//2), 
                           (int(monster[0]) - rect_width//4 - limb_size, int(monster[1]) + rect_height//2 + limb_size), limb_size)
            # 右下肢
            pygame.draw.line(WIN, color, (int(monster[0]) + rect_width//4, int(monster[1]) + rect_height//2), 
                           (int(monster[0]) + rect_width//4 + limb_size, int(monster[1]) + rect_height//2 + limb_size), limb_size)
            
            # 根据主语言绘制对应单词
            if monster[8] == 0:  # 英文怪物
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
    # 绘制死亡的怪物 - 只显示中文
    for monster in monsters:
        if monster[4]:
            chinese_text = FONT.render(monster[2][1], True, BLACK)
            chinese_rect = chinese_text.get_rect(center=(int(monster[0]), int(monster[1])))
            WIN.blit(chinese_text, chinese_rect)
    
    # 绘制子弹
    for bullet in bullets:
        if not bullet[6]:
            # 绘制子弹（增强可见性）
            # 外发光效果
            pygame.draw.circle(WIN, YELLOW, (int(bullet[0]), int(bullet[1])), 8)
            # 主子弹
            pygame.draw.circle(WIN, (255, 165, 0), (int(bullet[0]), int(bullet[1])), 5)
            # 绘制子弹上的完整单词（更大更明显）
            bullet_text = FONT.render(bullet[7], True, BLACK)
            bullet_rect = bullet_text.get_rect(center=(int(bullet[0]), int(bullet[1]) - 15))
            WIN.blit(bullet_text, bullet_rect)
    
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
    instruction_text1 = SMALL_FONT.render("左键移动玩家，右键发射最近怪物的第一个字母", True, BLACK)
    WIN.blit(instruction_text1, (WIDTH - 450, 20))
    instruction_text2 = SMALL_FONT.render("击中后抵消字母，全部抵消后怪物消灭", True, BLACK)
    WIN.blit(instruction_text2, (WIDTH - 450, 40))
    # 绘制难度设置
    difficulty_text = SMALL_FONT.render(f"难度: {current_difficulty}", True, BLACK)
    WIN.blit(difficulty_text, (20, 80))
    # 绘制难度切换提示
    difficulty_switch_text = SMALL_FONT.render("按1(简单), 2(中等), 3(困难)切换难度", True, BLACK)
    WIN.blit(difficulty_switch_text, (20, 110))
    
    pygame.display.update()

# 重置游戏
def reset_game():
    global player_x, player_y, monsters, bullets, score, game_over, frame_count, start_time
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    monsters = []
    bullets = []
    score = 0
    game_over = False
    frame_count = 0  # 重置帧计数器
    start_time = time.time()  # 重置游戏开始时间

# 主游戏循环
def main():
    global player_x, player_y, monsters, score, game_over, current_difficulty, frame_count, start_time
    frame_count = 0
    start_time = time.time()  # 记录游戏开始时间
    
    while True:
        clock.tick(FPS)
        frame_count += 1
        
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
            # 鼠标事件
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    if event.button == 1:  # 左键点击移动玩家
                        player_x, player_y = pygame.mouse.get_pos()
                        # 限制玩家在屏幕内
                        player_x = max(PLAYER_SIZE//2, min(WIDTH - PLAYER_SIZE//2, player_x))
                        player_y = max(PLAYER_SIZE//2, min(HEIGHT - PLAYER_SIZE//2, player_y))
                    elif event.button == 3:  # 右键点击发射子弹
                        shoot_bullet()
        
        # 移动怪物
        move_monsters()
        
        # 移动子弹
        move_bullets()
        
        # 移除死亡的怪物
        remove_dead_monsters()
        
        # 移除死亡的子弹
        remove_dead_bullets()
        
        # 绘制游戏
        draw_game()

if __name__ == "__main__":
    main()