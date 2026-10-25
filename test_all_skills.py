# coding=utf-8
import os
import subprocess

def main():
    # 设定 skills 所在的目录
    skills_dir = os.path.join(".agent", "skills")
    if not os.path.exists(skills_dir):
        print(f"找不到目录: {skills_dir}")
        return

    # 遍历所有 skills，找到所有的示例脚本（排除 base 文件）
    scripts_to_test = []
    for skill_name in os.listdir(skills_dir):
        examples_dir = os.path.join(skills_dir, skill_name, "examples")
        if os.path.isdir(examples_dir):
            for file_name in os.listdir(examples_dir):
                if file_name.endswith(".py") and not file_name.endswith("base.py"):
                    scripts_to_test.append(os.path.join(examples_dir, file_name))

    if not scripts_to_test:
        print("没有找到需要测试的 skill 动画脚本。")
        return

    print(f"一共找到了 {len(scripts_to_test)} 个需要测试的动画脚本！\n")

    # 循环执行 manim -pqh 命令
    for script in scripts_to_test:
        print("=" * 60)
        print(f"正在测试渲染: {script}")
        print("=" * 60)
        
        # 构建执行命令
        cmd = ["manim", "-pqh", script]
        
        try:
            # 运行命令，会等上一个跑完再跑下一个
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f">>> 渲染 {script} 时发生错误，返回码: {e.returncode}")
        except FileNotFoundError:
            print(">>> 错误: 找不到 manim 命令，请确认它是否在系统环境变量中。")
            break

    print("\n所有所有 skills 测试执行完成！")

if __name__ == "__main__":
    main()
