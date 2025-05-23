#importing necessary modules
import os
import ast
import sys
import time
import shutil
import uvicorn
import platform
import traceback
import threading
import subprocess
from datetime import datetime , timedelta
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request , Form
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Store ping results in a dictionary
ping_results = {}

# Flag to signal threads to exit
exit_flag = threading.Event()

# Defining the fastapi app and stored templates
app=FastAPI()

script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
templates_directory = os.path.join(script_directory,'templates')
templates = Jinja2Templates(directory=templates_directory)

# Adding middleware to the fastapi app to allow every client to access the API .
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_error_details(e):
    error_type = type(e).__name__
    error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
    error_filename = os.path.basename(traceback.extract_tb(e.__traceback__)[-1].filename)
    return f"{error_type} occurred in file {error_filename}, line {error_line}: {str(e)}"

def createFolder(custom_directory, file_name, data):
    # Get the directory where the script is located
    script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))

    file_date = datetime.now().strftime("%d-%m-%Y")

    # Combine the script directory and custom directory to create the full directory path
    full_directory = os.path.join(script_directory, custom_directory , file_date )

    try:
        if not os.path.exists(full_directory):
            os.makedirs(full_directory)

        with open(os.path.join(full_directory, f"{file_name}.txt"), "a+") as f:
            f.write(str(data)+"\n")

        # Deleting old log files
        old_date = (datetime.now() + timedelta(days=-5)).date()
        file_list = os.listdir(os.path.join(script_directory,custom_directory))
        for file in file_list:
            try:
                file_date = datetime.strptime(file, '%d-%m-%Y').date()
            except Exception:
                shutil.rmtree(os.path.join(script_directory, custom_directory ,  file))
            if file_date <= old_date:
                shutil.rmtree(os.path.join(script_directory, custom_directory , file))

        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        ip_file_path = os.path.join(script_directory,'ip_addresses.txt')
        with open(ip_file_path, 'r') as file:
            ip_addresses = file.read().splitlines()
        file_list = os.listdir(full_directory)
        for file in file_list:
            file = file.replace(".txt","")
            if file not in ip_addresses:
                os.remove(os.path.join(full_directory,file+".txt"))
                ping_results.pop(file)

    except Exception as e:
        print(f'Error: Creating directory {e}')

def stop_threads():
    try:
        exit_flag.set()  # Set the flag to signal threads to exit
        for thread in threading.enumerate():
            if thread.daemon:
                thread.join(timeout=1)  # Add a timeout to avoid getting stuck
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in stop_threads ->> {error_details}")
        return JSONResponse({error_details})
        
def start_ping_threads(ip_addresses):
    try:
        global exit_flag
        exit_flag = threading.Event()  # Reset the flag
        for ip in ip_addresses:
            threading.Thread(target=ping_worker, args=(ip,), daemon=True).start()
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error start_ping_threads ->> {error_details}")
        return JSONResponse({error_details})

# def is_reachable(ip_address,output):
#     return f"Reply from {ip_address}: bytes=" in output

# def extract_ping_statistics(output):
#     start = output.find("Ping statistics")
#     return output[start:]

def ping_worker(ip):
    while not exit_flag.is_set():
        try:
            if platform.system().lower() == "windows":
                output = subprocess.check_output(['ping', ip, '-n', '4']).decode()
            else:
                output = subprocess.check_output(['ping', ip, '-c', '4']).decode()

            start = output.find("Packets:")
            end = output.find("loss)")
            less_data = output[start:end] + "loss)"
            start_ = output.find("Minimum")
            end_ = output.find("loss)")
            less_data += f"\n{output[start_:]}"

            ping_results[ip] = {
                'ip_address': ip,
                'status': 'Reachable' if f"Reply from {ip}: bytes=" in output else 'Not Reachable',
                'statistics': output,
                'last_ping_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'less_data' : less_data
            }
            createFolder('Log/', ip, ping_results[ip])
        except subprocess.CalledProcessError as e:
            
            output = e.output.decode()
            
            start = output.find("Packets:")
            end = output.find("loss)")
            less_data = output[start:end] + "loss)"
            start_ = output.find("Minimum")
            end_ = output.find("loss)")
            less_data += f"\n{output[start_:]}"
            
            ping_results[ip] = {
                'ip_address': ip,
                'status': 'Not Reachable',
                'statistics': e.output.decode(),
                'last_ping_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'less_data' : less_data
            }
            createFolder('Log/', ip, ping_results[ip])

        time.sleep(10)

def start_process():
    try:
        # Start a thread for each IP address
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        file_path = os.path.join(script_directory,'ip_addresses.txt') # Replace with the path to your text file
        with open(file_path, 'r') as file:
            ip_addresses = file.read().splitlines()

        for ip in ip_addresses:
            threading.Thread(target=ping_worker, args=(ip,), daemon=True).start()
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in start_process ->> {error_details}")
        return JSONResponse({error_details})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/ping/live", response_class=HTMLResponse)
async def live_results(request: Request):
    print(f"Live --> {ping_results}")
    return templates.TemplateResponse("ping_results.html", {"request": request, "ping_results": ping_results})

@app.get("/ping/update_live_data")
async def live_results(request: Request):    
    return JSONResponse(content=ping_results)

@app.get("/ping/logs", response_class=HTMLResponse)
async def logs(request: Request):

    try:
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        full_directory = os.path.join(script_directory,'Log/')
        dirs = os.listdir(full_directory)
        
        # Implement your logs page here, if needed
        return templates.TemplateResponse("logs.html", {"request": request})
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in logs ->> {error_details}")
        return JSONResponse({error_details})

@app.get("/dirs")
async def list_directories(request: Request):
    
    try:
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        full_directory = os.path.join(script_directory, 'Log/')
        dirs = []
        for d in os.listdir(full_directory):
            if os.path.isdir(os.path.join(full_directory, d)):
                dir_path = os.path.join(full_directory, d)
                size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
                dirs.append({"directory": d, "size": size})
        print(f"Directory - {dirs}")
        return templates.TemplateResponse("load_dirs.html", {"request": request, "directories": dirs})
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in list_directories ->> {error_details}")
        return JSONResponse({error_details})
        
@app.get("/list_files/{directory}")
async def list_files(directory: str , request: Request):
    
    try:
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        full_directory = os.path.join(script_directory, 'Log', directory)
        files = []
        for file_name in os.listdir(full_directory):
            if file_name.endswith(".txt"):
                file_path = os.path.join(full_directory, file_name)
                file_size = os.path.getsize(file_path)
                files.append({"file_name": file_name.replace('.txt', ''), "size": file_size})
        return templates.TemplateResponse("file_list.html", {"request": request, "files": files, "directory": directory})
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in list_files ->> {error_details}")
        return JSONResponse({error_details})

@app.get("/read_file/{directory}/{file}")
async def read_file(directory: str, file: str,request: Request):

    try:
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        full_directory = os.path.join(script_directory, 'Log', directory)
        file_path = os.path.join(full_directory, f"{file}.txt")
        with open(file_path, "r") as file:
            i = 0
            file_data = {}
            for line in file:
                if line != '\n':
                    file_data[i] = ast.literal_eval(line.strip())
                i += 1
        return templates.TemplateResponse("file_data.html", {"request": request, "file_data": file_data})
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in read_file ->> {error_details}")
        return JSONResponse({error_details})

@app.get("/edit_ip")
async def read_ip(request: Request):
    
    try:
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        ip_file_path = os.path.join(script_directory,'ip_addresses.txt')
        with open(ip_file_path, "r") as f:
            ip_content = f.read()

        return templates.TemplateResponse(
            "edit_ip.html", {"request": request, "ip_content": ip_content}
        )
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in read_ip ->> {error_details}")
        return JSONResponse({error_details})
            
@app.post("/edit_ip")
async def save_ip(request: Request, edited_content: str = Form(...)):
    
    try:
        edited_content = edited_content.replace("\r", "")
        script_directory = os.path.dirname(os.path.realpath(__file__ or sys.argv[0]))
        ip_file_path = os.path.join(script_directory,'ip_addresses.txt')
        with open(ip_file_path, "w") as f:
            f.write(edited_content)

        # Stop existing threads and start new threads based on the updated IPs
        stop_threads()
        ping_results.clear()
        start_ping_threads(edited_content.splitlines())

        return templates.TemplateResponse("edit_ip.html", {"request": request, "ip_content": edited_content})
    except Exception as e:
        error_details = get_error_details(e)
        createFolder('Log/','error',f"Error in read_ip ->> {error_details}")
        return JSONResponse({error_details})

if __name__=="__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=5005,reload=True)