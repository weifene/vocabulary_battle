import pygame
import sys
import traceback

# 导入游戏模块
try:
    from word_monster import *
except Exception as e:
    print(f"导入错误: {e}")
    traceback.print_exc()
    sys.exit(1)

# 运行游戏并捕获所有错误
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"游戏崩溃: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        
        # 保存错误到文件
        with open('error_log.txt', 'w', encoding='utf-8') as f:
            f.write(f"游戏崩溃: {e}\n\n")
            f.write("详细错误信息:\n")
            traceback.print_exc(file=f)
        
        print("\n错误已保存到 error_log.txt")
        pygame.quit()
        sys.exit(1)
