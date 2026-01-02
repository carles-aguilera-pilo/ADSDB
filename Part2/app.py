import sys
import os
import subprocess

def usage():
    print("Usage: python app.py [COMMAND]")
    print("Supported commands:")
    print("-> full : Executes the pipeline and starts the frontend")
    print("-> frontend : Only executes the frontend, without starting the pipeline")
    print("-> pipeline : Only executes the pipeline, without starting the frontend")

def main():
    print(sys.argv)

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "full":
        subprocess.run(["python3", "pipeline.py"])
        os.environ["PYTHONPATH"] = '.'
        subprocess.run(["streamlit", "run", "src/frontend/Main_Page.py"])

    elif cmd == "frontend":
        subprocess.run(["streamlit", "run", "src/frontend/Main_Page.py"])

    elif cmd == "pipeline":
        os.environ["PYTHONPATH"] = '.'
        subprocess.run(["python3", "pipeline.py"])
        
    else:
        print(f"Unknown command: {cmd}")
        usage()


if __name__ == "__main__":
    main()
