#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置PYTHONPATH环境变量
os.environ['PYTHONPATH'] = '.'

# 导入并运行主应用
if __name__ == "__main__":
    from app.main import main
    import asyncio
    import sys
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)