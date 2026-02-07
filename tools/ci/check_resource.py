import sys

from typing import List
from pathlib import Path

from maa.resource import Resource
from maa.tasker import Tasker, LoggingLevelEnum


def check(dirs: List[Path]) -> bool:
    resource = Resource()

    print(f"Checking {len(dirs)} directories...")

    for dir in dirs:
        print(f"Checking {dir}...")
        status = resource.post_bundle(dir).wait().status
        if not status.succeeded:
            print(f"Failed to check {dir}.")
            return False

    print("All directories checked.")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python configure.py <directory>")
        sys.exit(1)

    Tasker.set_stdout_level(LoggingLevelEnum.All)
    dirs = [Path(arg) for arg in sys.argv[1:]]
    if sys.argv[1] != "base":
        # 如果不是检查base目录，添加base目录到检查列表
        base_dir = Path("assets/resource/base")
        if base_dir not in dirs:
            dirs.insert(0, base_dir)
            print(f"Added base directory to check list: {base_dir}")

    if not check(dirs):
        sys.exit(1)


if __name__ == "__main__":
    main()
