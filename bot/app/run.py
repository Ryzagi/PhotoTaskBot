import subprocess
import os


def run_scripts():
    # Define paths to the scripts
    app_script = os.path.join(os.path.dirname(__file__), 'app.py')
    tg_app_script = os.path.join(os.path.dirname(__file__), 'tg_app.py')

    # Start app.py
    app_process = subprocess.Popen(['python', app_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Started app.py")

    # Start tg_app.py
    tg_app_process = subprocess.Popen(['python', tg_app_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Started tg_app.py")

    try:
        # Wait for app.py to finish
        app_stdout, app_stderr = app_process.communicate()
        print("app.py finished")
        if app_stdout:
            print("app.py Output:", app_stdout.decode())
        if app_stderr:
            print("app.py Errors:", app_stderr.decode())

        # Wait for tg_app.py to finish
        tg_app_stdout, tg_app_stderr = tg_app_process.communicate()
        print("tg_app.py finished")
        if tg_app_stdout:
            print("tg_app.py Output:", tg_app_stdout.decode())
        if tg_app_stderr:
            print("tg_app.py Errors:", tg_app_stderr.decode())

    except KeyboardInterrupt:
        # If script is stopped, terminate both processes
        app_process.terminate()
        tg_app_process.terminate()
        print("Terminated both app.py and tg_app.py")


if __name__ == "__main__":
    run_scripts()
