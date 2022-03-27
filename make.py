import os
import subprocess
from pathlib import Path
import shutil

build_dir = Path("./build")
# shutil.rmtree(build_dir, ignore_errors=True)
build_dir.mkdir(exist_ok=True)
os.chdir(build_dir)
subprocess.run(["cmake", "../windowcapture_win_cpp"], check=True)
subprocess.run(["cmake", "--build", "."], check=True)
