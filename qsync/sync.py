import yaml
import os
import tarfile
import tempfile
import subprocess
import shutil
import sys
import re
import pathlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Iterator, Tuple, List, Dict, Any ,Callable ,Collection, Union


class Deduplicatable:
    """支持去重操作的抽象基类"""
    
    @staticmethod
    def deduplicate(items: List['Deduplicatable']) -> List['Deduplicatable']:
        """对项目列表进行去重操作
        
        Args:
            items: 需要去重的项目列表
            
        Returns:
            去重后的项目列表
        """
        # 检查列表是否为空
        if not items:
            return []
            
        # 检查首个元素的类型以决定使用哪种去重方法
        if isinstance(items[0], SitemapUpdateTask):
            return SitemapUpdateTask.deduplicate_sitemaps(items)
        else:
            # 使用集合来去除重复项，然后转回列表
            unique_items = list(set(items))
            return unique_items


class SitemapUpdateTask(Deduplicatable):
    """表示站点地图更新任务的类"""
    
    def __init__(self, path: str, loc: List[str], root_path: str = None):
        """
        初始化站点地图更新任务
        
        Args:
            path: 站点地图路径
            loc: 位置列表
            root_path: 根路径，用于计算相对路径
        """
        # 使用pathlib统一路径形式
        self.path = str(pathlib.Path(path).resolve())
        # 保存相对路径用于显示
        if root_path:
            try:
                self.relative_path = str(pathlib.Path(path).relative_to(pathlib.Path(root_path)))
            except ValueError:
                # 如果path不在root_path下，则使用原始路径
                self.relative_path = path
        else:
            self.relative_path = path
        # 确保loc是一个列表的副本，防止外部修改影响内部状态
        self.loc = list(loc) if loc else []
    
    def __str__(self):
        return f"SitemapUpdateTask(relative_path='{self.relative_path}', loc={self.loc})"
    
    def __repr__(self):
        return f"SitemapUpdateTask(relative_path='{self.relative_path}', loc={self.loc!r})"
    
    def __eq__(self, other):
        """重载 == 操作符，仅比较统一形式的path"""
        if not isinstance(other, SitemapUpdateTask):
            return False
        return self.path == other.path
    
    def __hash__(self):
        """重载 hash() 函数，基于统一形式的path计算哈希"""
        return hash(str(self.path))
    
    def run(self):
        """执行站点地图更新任务"""
        # 使用pathlib处理路径
        sitemap_path = pathlib.Path(self.path)
        
        # 如果文件不存在，则创建一个新的站点地图
        if not sitemap_path.exists():
            self._create_new_sitemap(sitemap_path)
        
        # 解析并更新现有的站点地图
        self._update_sitemap(sitemap_path)
    
    def _create_new_sitemap(self, sitemap_path: pathlib.Path):
        """创建新的站点地图文件"""
        print(f"创建新的站点地图文件: {self.relative_path}")
        
        # 创建根元素，使用命名空间
        urlset = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
        
        # 为每个位置添加URL条目
        for location in self.loc:
            url = ET.SubElement(urlset, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            loc = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            loc.text = location
            lastmod = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            lastmod.text = datetime.now().strftime("%Y-%m-%d")
            changefreq = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq")
            changefreq.text = "weekly"
            priority = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}priority")
            priority.text = "0.8"
        
        # 创建XML树并保存
        tree = ET.ElementTree(urlset)
        # 确保目录存在
        sitemap_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(str(sitemap_path), encoding="utf-8", xml_declaration=True)
    
    def _update_sitemap(self, sitemap_path: pathlib.Path):
        """更新现有的站点地图文件"""
        print(f"更新站点地图文件: {self.relative_path}")
        
        # 解析现有的站点地图
        try:
            tree = ET.parse(str(sitemap_path))
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"警告: 无法解析站点地图文件 {self.relative_path}: {e}，已跳过更新")
            return
        
        # 获取当前日期
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 查找现有的URL条目并更新它们的日期
        existing_urls = {}
        for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc_elem = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if loc_elem is not None and loc_elem.text:
                existing_urls[loc_elem.text] = url
        
        # 更新现有URL的日期或添加新URL
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        for location in self.loc:
            if location in existing_urls:
                # 更新现有URL的lastmod日期
                url = existing_urls[location]
                lastmod = url.find(f"{namespace}lastmod")
                if lastmod is not None:
                    lastmod.text = today
                else:
                    lastmod = ET.SubElement(url, f"{namespace}lastmod")
                    lastmod.text = today
                print(f"已更新URL的日期: {location}")
            else:
                # 添加新的URL条目
                url = ET.SubElement(root, f"{namespace}url")
                loc = ET.SubElement(url, f"{namespace}loc")
                loc.text = location
                lastmod = ET.SubElement(url, f"{namespace}lastmod")
                lastmod.text = today
                changefreq = ET.SubElement(url, f"{namespace}changefreq")
                changefreq.text = "weekly"
                priority = ET.SubElement(url, f"{namespace}priority")
                priority.text = "0.8"
                print(f"已添加新URL: {location}")
        
        # 保存更新后的站点地图
        tree.write(str(sitemap_path), encoding="utf-8", xml_declaration=True)

    @staticmethod
    def deduplicate_sitemaps(items: List['SitemapUpdateTask']) -> List['SitemapUpdateTask']:
        """专门用于站点地图任务的去重方法
        
        Args:
            items: SitemapUpdateTask对象列表
            
        Returns:
            去重并合并后的SitemapUpdateTask对象列表
        """
        if not items:
            return []
        
        # 使用字典按path分组
        path_dict = {}
        for item in items:
            if item.path in path_dict:
                # 合并loc列表，去重
                existing_locs = set(path_dict[item.path].loc)
                new_locs = set(item.loc)
                merged_locs = list(existing_locs.union(new_locs))
                path_dict[item.path].loc = merged_locs
            else:
                # 创建新的条目，保留root_path信息
                path_dict[item.path] = SitemapUpdateTask(item.path, item.loc, 
                                                         getattr(item, 'relative_path', None))
        
        # 返回去重后的列表
        return list(path_dict.values())


class ShellCmd(Deduplicatable):
    """表示一个shell命令的类，支持哈希和比较操作"""
    def __init__(self, cmd: str):
        # 标准化命令：去除首尾空格，将多个连续空格替换为单个空格
        self.cmd = re.sub(r'\s+', ' ', cmd.strip())

    def __str__(self):
        if isinstance(self.cmd, tuple):
            return ' '.join(self.cmd)
        return self.cmd

    def __repr__(self):
        return f'ShellCmd({self.cmd!r})'

    def __eq__(self, other):
        if not isinstance(other, ShellCmd):
            return False
        return self.cmd == other.cmd

    def __hash__(self):
        return hash(self.cmd)

class FilesMapping:
    """文件映射基类，用于迭代获取文件映射的根路径、源路径和目标路径"""
    
    def __iter__(self) -> Iterator[Tuple[str, str, str]]:
        """返回迭代器，每次迭代返回 (project_root, local_path, remote_path)"""
        raise NotImplementedError


def _resolve_symlinks(project_root: str, local_path: str, remote_path: str, visited: set = None) -> Tuple[str, str, str]:
    """
    递归解析软链接的辅助函数
    
    Args:
        project_root: 项目根目录
        local_path: 本地路径
        remote_path: 远程路径
        visited: 已访问路径集合，防止循环链接
        
    Return:
        (project_root, local_path, remote_path) 元组
    """
    if visited is None:
        visited = set()
    
    full_local_path = os.path.join(project_root, local_path)
    
    # 防止循环链接
    abs_path = os.path.abspath(full_local_path)
    if abs_path in visited:
        print(f"警告: 检测到循环链接 {full_local_path}，跳过")
        return
    
    visited.add(abs_path)
    
    # 检查路径是否存在
    if not os.path.exists(full_local_path): #and not os.path.islink(full_local_path)
        print(f"警告: 路径 {full_local_path} 不存在，跳过")
        return 
    
    # 如果是软链接，解析它
    if os.path.islink(full_local_path):
        try:
            target = os.readlink(full_local_path)
            # 处理以 \\?\ 开头的 Windows 路径
            if target.startswith('\\\\?\\'):
                target = target[4:]  # 移除 \\?\ 前缀
            # print(f"解析软链接 {full_local_path} -> {target}")
            # 处理相对链接
            if not os.path.isabs(target):
                target = os.path.join(os.path.dirname(full_local_path), target)
            
            
            return _resolve_symlinks('', target, remote_path, visited.copy())
        except OSError as e:
            print(f"警告: 无法读取链接 {full_local_path}: {e}")
            return
    # 如果是文件
    elif os.path.isfile(full_local_path):
        return (project_root, local_path, remote_path)
    # 如果是目录
    elif os.path.isdir(full_local_path):
        raise
    
    # 移除当前路径（回溯）
    visited.discard(abs_path)


class FileMapping(FilesMapping, Deduplicatable):
    """单个文件映射类，支持软链接解析"""
    
    def __init__(self, project_root: str, local_path: str, remote_path: str):
        self.project_root = project_root
        self.local_path = local_path
        self.remote_path = remote_path
    
    def __iter__(self) -> Iterator[Tuple[str, str, str]]:
        """返回包含单个文件映射的迭代器，支持软链接解析"""
        yield _resolve_symlinks(self.project_root, self.local_path, self.remote_path)
    
    def __eq__(self, other):
        """重载 == 操作符，比较本地路径和远程路径"""
        if not isinstance(other, FileMapping):
            return False
        return (self.project_root == other.project_root and 
                self.local_path == other.local_path and 
                self.remote_path == other.remote_path)
    
    def __hash__(self):
        """重载 hash() 函数，基于本地路径和远程路径计算哈希"""
        return hash((self.project_root, self.local_path, self.remote_path))


class DirMapping(FilesMapping):
    """目录映射类，支持软链接解析"""
    
    def __init__(self, project_root: str, local_path: str, remote_path: str):
        self.project_root = project_root
        self.local_path = local_path
        self.remote_path = remote_path
    
    def __iter__(self) -> Iterator[Tuple[str, str, str]]:
        """返回目录中所有文件的映射迭代器"""
        full_local_path = os.path.join(self.project_root, self.local_path)
        if os.path.isdir(full_local_path):
            # 确保远程路径以/结尾
            remote_path = self.remote_path.rstrip('/') + '/'
            for root, _, files in os.walk(full_local_path):
                for file in files:
                    file_path = os.path.join(root, file).replace('\\', '/')
                    rel_path = os.path.relpath(file_path, full_local_path).replace('\\', '/')
                    arcname = os.path.join(remote_path, rel_path).replace('\\', '/')
                    # 计算相对于项目根目录的路径
                    local_rel_path = os.path.relpath(file_path, self.project_root).replace('\\', '/')
                    yield _resolve_symlinks(self.project_root, local_rel_path, arcname)
        else:
            print(f"警告: 目录 {full_local_path} 不存在，跳过")



def load_config(config_path: str, visited_paths: set = None) -> dict:
    """加载YAML配置文件，支持递归包含其他配置文件"""
    
    # 初始化访问路径集合
    if visited_paths is None:
        visited_paths = set()
    
    # 获取绝对路径以避免重复加载
    abs_config_path = os.path.abspath(config_path)
    
    # 检查是否已经访问过该配置文件（防止循环引用）
    if abs_config_path in visited_paths:
        raise ValueError(f"检测到循环引用的配置文件: {abs_config_path}")
    
    # 添加到已访问路径集合
    visited_paths.add(abs_config_path)
    
    # 加载当前配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 检查配置文件是否成功加载
    if config is None:
        config = {}
        print(f"警告: 配置文件 {config_path} 为空或加载失败，已跳过")
    
    config['_file_mappings'] = create_file_mappings(config.get('resources',{}), config.get('project_root', ''))
     # 处理站点地图更新任务。
    sitemap_tasks = []
    deduplicatable_files = []  # 用于存储sitemap文件映射的列表
    if config.get('sitemaps', []):
        # print("处理站点地图更新任务...")
        for sitemap in config.get('sitemaps', []):
            # 每个sitemap应该是一个字典，包含path和loc键
            if 'path' in sitemap and 'loc' in sitemap:
                # 确保loc是列表格式，如果不是则转换为列表
                loc = sitemap['loc']
                if isinstance(loc, str):
                    raise ValueError(f"站点地图配置项 {sitemap} 中的loc键值 {loc} 不是列表格式")
                sitemap_task = SitemapUpdateTask(sitemap['path'], loc)
                sitemap_tasks.append(sitemap_task)
                
                # 如果有target配置项，则添加到deduplicatable_files列表中
                if 'target' in sitemap:
                    target = sitemap['target']
                    # 创建文件映射并添加到deduplicatable_files列表中
                    file_mapping = FileMapping('', sitemap['path'], target)
                    deduplicatable_files.append(file_mapping)
            else:
                print(f"警告: 无效的站点地图配置项 {sitemap}，缺少必需的path或loc键")
        
    config['_all_sitemaps'] = sitemap_tasks
    config['_deduplicatable_files'] = deduplicatable_files
    
    # 如果没有include项，直接返回配置
    if 'include' not in config:
        visited_paths.remove(abs_config_path)  # 移除当前路径
        return config
    
    # 递归加载所有包含的配置文件
    included_configs = []
    for include_path in config['include']:
        # 解析相对路径
        if not os.path.isabs(include_path):
            include_path = os.path.join(config.get('project_root', ''), include_path)
        
        # 递归加载包含的配置文件
        included_config = load_config(include_path, visited_paths)
        print(f"成功加载包含配置文件: {include_path}")
        included_configs.append(included_config)
    
    # 移除当前路径（回溯）
    visited_paths.remove(abs_config_path)
    
    def _merge_listdict(ds:List[Dict[str, List[Any]]], keys:List[str]) -> Dict[str, List[Any]]:
        """合并字典中的指定键"""
        merged=ds[-1].copy()
        for key in keys:
            vs=[]
            for d in ds:
                if (key in d) and (d[key] is not None):
                    vs.extend(d[key])   
            if vs:
                if isinstance(vs[0], Deduplicatable):
                    vs = Deduplicatable.deduplicate(vs)
                merged[key]=vs
        return merged
    return _merge_listdict(
        included_configs+[config],
        [
            'pre_commands',
            'local_pre_commands',
            '_file_mappings',
            'post_commands',
            'local_post_commands',
            '_all_sitemaps',
            '_deduplicatable_files'
        ]
    )
def create_file_mappings(resources: Dict[str,Dict[str,str]], project_root: str) -> List[FilesMapping]:
    """创建所有文件和目录的映射"""
    # 先收集所有文件映射
    file_mappings = []
    
    # 收集文件映射
    for local_path, remote_path in resources.get('files', {}).items():
        file_mapping = FileMapping(project_root, local_path, remote_path)
        file_mappings.append(file_mapping)
    
    # 收集目录映射
    for local_path, remote_path in resources.get('dirs', {}).items():
        dir_mapping = DirMapping(project_root, local_path, remote_path)
        file_mappings.append(dir_mapping)
    return file_mappings
def create_tar_archive(file_mappings: List[FilesMapping], temp_dir: str) -> str:
    """创建包含所有资源的tar.gz文件"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tar_path = os.path.join(temp_dir, f"deploy_{timestamp}.tar.gz")
    
    # 统一处理所有文件映射
    with tarfile.open(tar_path, "w:gz") as tar:
        last_root = None
        for mapping in file_mappings:
            for item in mapping:
                if item is None:
                    continue
                root, src_path, dst_path = item
                full_local_path = os.path.join(root, src_path)
                if root != last_root:
                    last_root = root
                    if root:
                        print(f"{root}:")
                if os.path.exists(full_local_path):
                    tar.add(full_local_path, arcname=dst_path)
                    print(f"添加文件: {src_path} -> {dst_path}")
                else:
                    print(f"警告: 文件 {full_local_path} 不存在，跳过")
    
    return tar_path

def sync(config_path):
    """执行部署流程"""
    config = load_config(config_path)
    remote_host = config['remote_host']
    temp_dir = config.get('temp_dir', '/tmp')
    # 创建文件映射
    file_mappings = config.get('_file_mappings', [])
    pre_commands = config.get('pre_commands', [])
    post_commands = config.get('post_commands', [])
    local_pre_commands = config.get('local_pre_commands', [])
    local_post_commands = config.get('local_post_commands', [])
    sitemap_tasks = config.get('_all_sitemaps', [])
    deduplicatable_files = config.get('_deduplicatable_files', [])
    
    # 将deduplicatable_files添加到file_mappings中
    file_mappings.extend(deduplicatable_files)
    
    # 处理站点地图更新任务。
    if sitemap_tasks:
        print("处理站点地图更新任务...")        
        # 执行每个站点地图更新任务
        for task in sitemap_tasks:
            # print(f"执行站点地图更新任务: {task.path}")
            task.run()
    
    # 执行本地预处理命令
    if local_pre_commands:
        print("执行本地预处理命令...")
        # 去重本地预处理命令
        local_pre_cmd_objects = [ShellCmd(cmd) for cmd in local_pre_commands]
        unique_local_pre_commands = ShellCmd.deduplicate(local_pre_cmd_objects)
        # 执行每个命令
        for cmd in unique_local_pre_commands:
            cmd_str = str(cmd)
            print(f"> {cmd_str}")
            subprocess.run(cmd_str, shell=True, check=True)
    
    # 执行远程预处理命令
    if pre_commands:
        print("执行远程预处理命令...")
        # 去重预处理命令
        pre_cmd_objects = [ShellCmd(cmd) for cmd in pre_commands]
        unique_pre_commands = ShellCmd.deduplicate(pre_cmd_objects)
        # 转换回字符串列表
        pre_cmd_strings = [str(cmd) for cmd in unique_pre_commands]
        ssh_command = ['ssh', remote_host, '; '.join(pre_cmd_strings)]
        print("$"+' '.join(ssh_command))
        subprocess.run(ssh_command, check=True)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as local_temp_dir:
        # 创建tar包
        tar_path = create_tar_archive(file_mappings, local_temp_dir)
        tar_name = os.path.basename(tar_path)
        remote_tar_path = os.path.join(temp_dir, tar_name).replace('\\', '/')
        
        # 传输tar包
        scp_command = ['scp', tar_path, f"{remote_host}:{remote_tar_path}"]
        print("$"+' '.join(scp_command))
        subprocess.run(scp_command, check=True)
        
        # 构建远程命令
        remote_commands = [
            f"tar -xzf {remote_tar_path} -C /",
            f"rm {remote_tar_path}"
        ]
        
        # 使用 ShellCmd 类和 deduplicate 方法对后处理命令去重
        if post_commands:
            # 去重后处理命令
            post_cmd_objects = [ShellCmd(cmd) for cmd in post_commands]
            unique_post_commands = ShellCmd.deduplicate(post_cmd_objects)
            # 转换回字符串列表
            post_cmd_strings = [str(cmd) for cmd in unique_post_commands]
            remote_commands.extend(post_cmd_strings)
        
        # 执行远程命令
        ssh_command = ['ssh', remote_host, '; '.join(remote_commands)]
        print("$"+' '.join(ssh_command))
        subprocess.run(ssh_command, check=True)
    
    # 执行本地后处理命令
    if local_post_commands:
        print("执行本地后处理命令...")
        # 去重本地后处理命令
        local_post_cmd_objects = [ShellCmd(cmd) for cmd in local_post_commands]
        unique_local_post_commands = ShellCmd.deduplicate(local_post_cmd_objects)
        # 执行每个命令
        for cmd in unique_local_post_commands:
            cmd_str = str(cmd)
            print(f"> {cmd_str}")
            subprocess.run(cmd_str, shell=True, check=True)
    
    print("部署完成!")

def main():
    if len(sys.argv) != 2:
        print("用法: python sync.py <config_path>")
        sys.exit(1)
    
    for config_path in sys.argv[1:]:
        sync(config_path)
if __name__ == "__main__":
    main()