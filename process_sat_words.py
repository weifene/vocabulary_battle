import json
import codecs

# 读取JSON文件
json_path = r'C:\Users\Administrator\AppData\Local\Temp\MicrosoftEdgeDownloads\9b7ebc50-4169-4bd4-8555-a7d5d4f44f59\SAT_3.json'
output_path = r'D:\qlib\word_monster_game\kaoyan_words.txt'

with codecs.open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

word_count = 0

with codecs.open(output_path, 'w', encoding='utf-8') as out_f:
    for item in data:
        word = item.get('headWord', '')
        content = item.get('content', {})
        word_info = content.get('word', {})
        word_content = word_info.get('content', {})
        
        # 提取中文释义（从trans数组中）
        trans = word_content.get('trans', [])
        chinese_meaning = ""
        if trans:
            chinese_meaning = trans[0].get('tranCn', '')
        
        # 提取英文例句和中文例句
        sentence = word_content.get('sentence', {})
        sentences = sentence.get('sentences', [])
        
        english_sentence = ""
        chinese_sentence = ""
        
        if sentences:
            # 取第一个例句
            first_sentence = sentences[0]
            english_sentence = first_sentence.get('sContent', '')
            chinese_sentence = first_sentence.get('sCn', '')
            
            # 只取前100个字符
            if len(english_sentence) > 100:
                english_sentence = english_sentence[:100]
            if len(chinese_sentence) > 100:
                chinese_sentence = chinese_sentence[:100]
        
        # 如果没有找到例句，生成一个简单的
        if not english_sentence:
            english_sentence = f"The {word} is very important."
        
        # 如果没有找到中文释义，使用单词本身
        if not chinese_meaning:
            chinese_meaning = word
        
        # 写入文件（格式：单词\t释义\t英文例句\t中文例句）
        output_line = f"{word}\t{chinese_meaning}\t{english_sentence}\t{chinese_sentence}\n"
        out_f.write(output_line)
        word_count += 1
        
        if word_count >= 100:
            break

print(f"成功处理 {word_count} 个单词！")
print(f"文件已保存到: {output_path}")
