# -*- coding: utf-8 -*-
# 检查MySQL数据库连接和数据

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pymysql
    print("✓ pymysql已安装")
except ImportError:
    print("✗ pymysql未安装，请运行: pip install pymysql")
    sys.exit(1)

from config.db_config import mysql_db_config

print("\nMySQL连接配置:")
print(f"  主机: {mysql_db_config['host']}")
print(f"  端口: {mysql_db_config['port']}")
print(f"  用户名: {mysql_db_config['user']}")
print(f"  数据库: {mysql_db_config['db_name']}")
print(f"  密码: {'*' * len(mysql_db_config['password'])}")

try:
    # 连接MySQL
    conn = pymysql.connect(
        host=mysql_db_config['host'],
        user=mysql_db_config['user'],
        password=mysql_db_config['password'],
        database=mysql_db_config['db_name'],
        port=mysql_db_config['port'],
        charset='utf8mb4'
    )
    print("\n✓ MySQL连接成功!")
    
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\n数据库中的表 ({len(tables)} 个):")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查bilibili_video表数据
    if ('bilibili_video',) in tables:
        cursor.execute("SELECT COUNT(*) FROM bilibili_video")
        video_count = cursor.fetchone()[0]
        print(f"\n✓ bilibili_video 表中有 {video_count} 条视频数据")
        
        if video_count > 0:
            cursor.execute("SELECT video_id, title, nickname FROM bilibili_video LIMIT 5")
            videos = cursor.fetchall()
            print("\n前5条视频数据:")
            for video in videos:
                print(f"  - {video[0]}: {video[1][:50]}... (作者: {video[2]})")
    else:
        print("\n✗ bilibili_video 表不存在")
    
    # 检查bilibili_video_comment表数据
    if ('bilibili_video_comment',) in tables:
        cursor.execute("SELECT COUNT(*) FROM bilibili_video_comment")
        comment_count = cursor.fetchone()[0]
        print(f"\n✓ bilibili_video_comment 表中有 {comment_count} 条评论数据")
    else:
        print("\n✗ bilibili_video_comment 表不存在")
    
    # 检查bilibili_up_info表数据
    if ('bilibili_up_info',) in tables:
        cursor.execute("SELECT COUNT(*) FROM bilibili_up_info")
        creator_count = cursor.fetchone()[0]
        print(f"\n✓ bilibili_up_info 表中有 {creator_count} 条创作者数据")
    else:
        print("\n✗ bilibili_up_info 表不存在")
    
    conn.close()
    print("\n✓ 检查完成!")
    
except pymysql.Error as e:
    print(f"\n✗ MySQL连接失败: {e}")
    print("\n请检查:")
    print("  1. MySQL服务是否运行")
    print("  2. 数据库连接配置是否正确 (config/db_config.py)")
    print("  3. 数据库是否已创建")
    print("  4. 用户名和密码是否正确")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

