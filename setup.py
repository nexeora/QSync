"""qsync 包的安装配置文件"""

from setuptools import setup, find_packages
import os

# 从 requirements.in 读取依赖
with open('requirements.in', 'r', encoding='utf-8') as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 读取 README.md 内容
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return '一个用于文件同步和部署的工具'

setup(
    name='qsync',
    version='1.0.0',  
    author='Nexeora',   
    author_email='nexeora@outlook.com',  
    description='一个用于文件同步和部署的工具',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/nexeora/qsync',  # 项目URL占位符，待后续填写
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'qsync=qsync.sync:main',  # CLI 命令 qsync，入口点为 qsync.sync 模块的 main 函数
        ],
    },
)