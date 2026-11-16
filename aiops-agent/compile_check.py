"""编译检查脚本"""
import py_compile
import sys
from pathlib import Path

def compile_dir(dir_path):
    """编译目录下的所有 Python 文件"""
    errors = []
    files = list(Path(dir_path).rglob("*.py"))
    
    for file in files:
        try:
            py_compile.compile(str(file), doraise=True)
            print(f"✓ {file.relative_to(Path.cwd())}")
        except py_compile.PyCompileError as e:
            errors.append((file, str(e)))
            print(f"✗ {file.relative_to(Path.cwd())}: {e}")
    
    return errors

if __name__ == "__main__":
    print("编译检查应用层...")
    errors = compile_dir("application")
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误")
        sys.exit(1)
    else:
        print(f"\n✅ 编译成功")
        sys.exit(0)
