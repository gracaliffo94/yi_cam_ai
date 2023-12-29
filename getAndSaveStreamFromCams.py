import cv2
from ultralytics import YOLO
from datetime import datetime
import os
import socket

BASE_SYSTEM_FOLDER = "CamSystem"
FPS_RATE = 2
MAX_SECONDS_RETRY_RTSP_AGAINST_SAME_IP = 120
SECONDS_INTERVAL_BETWEEN_MAIN_SPAWNINGS = 0
STREAM_PATH_OK = "LOGS_OK"
STREAM_PATH_NOK = "LOGS_NOK"
RTSP_U = "gra"
RTSP_P = "gra"

import threading
import time

def get_custom_name(ip_address):
    try:
        # Attempt a reverse DNS lookup
        custom_name, _, _ = socket.gethostbyaddr(ip_address)
        return custom_name
    except socket.herror as e:
        print(f"Error: {e}")
        return None

def get_unconnected_hosts_ip():
    # Example usage:
    unconnected_hosts_ip = []
    for i in range(2, 255):
        ip_to_lookup = "192.168.1." + str(i)  # Replace with the IP address you want to lookup
        custom_name = get_custom_name(ip_to_lookup)
        # If the custom_name is the same as the ip, then this host is unconnected
        if ip_to_lookup == custom_name:
            unconnected_hosts_ip.append(ip_to_lookup)
    return unconnected_hosts_ip

def create_stream_dirs_ifne(directory_name, cam_ip):
    # str just to be sure
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
        print(f"New RTSP cam detected! IP --->" + cam_ip) if ("SUCCES" in directory_name) else None
    else:
        print(f"Restarted RTSP connection with --->" + cam_ip) if ("SUCCES" in directory_name) else None

def create_main_cam_folder(directory_name):
    # str just to be sure
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
        print(f"First time for this system!")
    else:
        print(f"System (re)started")


def get_host_name(myTargetIp):
    # If the host doesn't have a custom name or it is not connected (strange perchè sennò non stavamo eseguendo sta funzione, ma vabbè)
    # This function returns empty string (there is no name!)
    # Otherwise, this function returns its hostname (without .homenet.telecomitalia.it)
    custom_name, _, _ = socket.gethostbyaddr("192.168.1." + myTargetIp)
    if "192.168.1" in custom_name:
        return ""
    return custom_name.split(".")[0]


class RTSPConnectionThread(threading.Thread):
    def __init__(self, myTargetIp, cap):
        super(RTSPConnectionThread, self).__init__()
        self.myTargetIp = myTargetIp
        self.myCap = cap

    def run(self):
        myTargetIp = str(self.myTargetIp)
        print("[THREAD "+myTargetIp+"] Spawn! :)")
        cap = self.myCap

        # If the host doesn't have a custom name or it is not connected
        # Then we don't use its name and we call its folder just with its last ip number.
        # Otherwise we concat its name to the folder name
        target_hostname = get_host_name(myTargetIp)
        BASE_THREAD_PATH = BASE_SYSTEM_FOLDER + "/" + target_hostname


        directory_log_for_reconnection_failure = BASE_THREAD_PATH + "/" + "EMPTY_CAPTURE_RECONNECTION_FAILURE"
        directory_log_for_reconnection_success = BASE_THREAD_PATH + "/" + "EMPTY_CAPTURE_RECONNECTION_SUCCESS"
        my_directory_name = BASE_THREAD_PATH + "/" + "Stream"
        create_stream_dirs_ifne(my_directory_name, myTargetIp)
        create_stream_dirs_ifne(directory_log_for_reconnection_failure, myTargetIp)
        create_stream_dirs_ifne(directory_log_for_reconnection_success, myTargetIp)

        while True:
            print("[THREAD "+myTargetIp+"] new cycle ")
            ret, frame = cap.read()

            # If we reached this point, then ret shouldn't be False and the frame shouldn't be empty.
            # But on the other hand, sometimes during the loop there is some failure, it could be due to many reasons:
            # network, low computational power of the edge device that maybe raise timeouts, eccecc (idk)...
            # So, we try for 60 seconds to connect to the same IP, so that if it is a temporary and not a real problem
            # we are able to connect quickly again and get the stream.

            if not ret:
                now_string = str(datetime.now()).replace(":", ".")
                print("******ERROR EMPTY RET AT "+now_string+"******")
                start_time = time.time()
                while True:
                    end_time = time.time()
                    now_string = str(datetime.now()).replace(":", ".")
                    ret, frame = cap.read()

                    if not ret:
                        delta_time_seconds = end_time - start_time
                        if delta_time_seconds > MAX_SECONDS_RETRY_RTSP_AGAINST_SAME_IP:
                            with open(directory_log_for_reconnection_failure + "/" + now_string + ".txt", "w") as outfile:
                                outfile.write("WAS OFFLINE FOR " + str(delta_time_seconds) + ".\nGiving up because max time:" + str(MAX_SECONDS_RETRY_RTSP_AGAINST_SAME_IP) + ".")
                            # This return ends the life of this Thread. RIP :(
                            return
                        continue

                    # If we reach this line, then we succeeded in getting the frames again. Yuppie!
                    with open(directory_log_for_reconnection_success + "/" + now_string + ".txt", "w") as outfile:
                        outfile.write("WAS OFFLINE FOR A DELTA OF " + str(delta_time_seconds) + ".\nI didn't give up because max time:" + str(MAX_SECONDS_RETRY_RTSP_AGAINST_SAME_IP) + ".")
                    break

            frame = cv2.resize(frame, (960, 540))
            now_string = str(datetime.now()).replace(":", ".")
            cv2.imwrite(my_directory_name+"/"+now_string+".jpg",frame)
            sleep_time = float(1)/float(FPS_RATE)
            time.sleep(sleep_time)

def main(args):
    threads = {}
    iteration_counter = 0
    while (True):
        iteration_counter += 1
        with open(BASE_SYSTEM_FOLDER + "/" + "REPORT" + ".txt", "a") as outfile:
            report_iteration_string = "*********  ITERATION " + str(iteration_counter) + "  *********"
            print(report_iteration_string)
            outfile.write(report_iteration_string)

        now_string = str(datetime.now()).replace(":", ".")
        report_just_connected_threads_string = "[CONNECTED AT THIS ITERATION] At " + now_string + " the threads managing these ips have been spawn:"
        report_unconnected_ips_string = "[UNCONNECTED] At " + now_string + " skipping unconnected ips:"
        report_connected_threads_string = "[CONNECTED AND CHECKED OK] At " + now_string + " the threads:"
        report_not_cam_ips_string = "[NOT A CAM] At " + now_string + " the ip addresses:"
        report_dead_threads_string = "[DEAD THREADS] At " + now_string + " the threads at the ips:"

        print("[DEBUG] Getting unconnected ip list ...")
        unconnected_hosts_ip_list = get_unconnected_hosts_ip()
        print("... this is the list:" + str(unconnected_hosts_ip_list))

        dead_threads_count = 0
        threads_handles = list(threads.keys())
        for ip in threads_handles:
            if not threads[ip].is_alive():
                dead_threads_count +=1
                report_dead_threads_string += " " + ip
                threads.pop(ip)

        if dead_threads_count > 0:
            with open(BASE_SYSTEM_FOLDER + "/" + "REPORT" + ".txt", "a") as outfile:
                report_dead_threads_string += " are dead. RIP :( \n"
                print(report_dead_threads_string)
                outfile.write(report_dead_threads_string)

        for current_ip in range(2, 255):
            current_ip = str(current_ip)
            current_full_ip_address = "192.168.1." + current_ip

            # Skip this ip if there is no associated host
            if current_full_ip_address in unconnected_hosts_ip_list:
                report_unconnected_ips_string += " " + current_ip
                continue

            # Skip this ip if there is already a thread working on this
            if current_ip in threads.keys():
                report_connected_threads_string += " " + current_ip
                continue

            cap = cv2.VideoCapture('rtsp://' + RTSP_U + ":" + RTSP_P + '@' + current_full_ip_address + ':554/ch0_0.h264',)  # IP Camera

            # If cap is not open, then probably at this ip there is not a YI cam. Then, skip this ip
            if not cap.isOpened():
                report_not_cam_ips_string += " " + current_full_ip_address
                continue

            # If we didn't skip this ip so far, then most likely it is a YI cam (or any other device sending rtsp on 554 with my user and pass... :))
            current_thread = RTSPConnectionThread(current_ip, cap)
            threads[current_ip] = current_thread
            current_thread.start()
            report_just_connected_threads_string += " " + current_full_ip_address


        with open(BASE_SYSTEM_FOLDER + "/" + "REPORT" + ".txt", "a") as outfile:
            report_just_connected_threads_string += " the say - Hello World! - :) . Excellent :D \n"
            print(report_just_connected_threads_string)
            outfile.write(report_just_connected_threads_string)

        with open(BASE_SYSTEM_FOLDER + "/" + "REPORT" + ".txt", "a") as outfile:
            report_unconnected_ips_string += " are unconnected.\n"
            print(report_unconnected_ips_string)
            outfile.write(report_unconnected_ips_string)

        with open(BASE_SYSTEM_FOLDER + "/" + "REPORT" + ".txt", "a") as outfile:
            report_connected_threads_string += " are connected and seem to work fine. Yuppie! :) \n"
            print(report_connected_threads_string)
            outfile.write(report_connected_threads_string)

        with open(BASE_SYSTEM_FOLDER + "/" + "REPORT" + ".txt", "a") as outfile:
            report_not_cam_ips_string += " are connected to the LAN but they are NOT cameras. Good :| \n"
            print(report_not_cam_ips_string)
            outfile.write(report_not_cam_ips_string)

        time.sleep(SECONDS_INTERVAL_BETWEEN_MAIN_SPAWNINGS)
        # --------------------------------------------------------------------------------------------------------
        '''
        frame = cv2.resize(frame, (960, 540))
        # Run inference on an image

        model = YOLO("./yolov8l.pt")
        results = model.predict(source=frame, show=False)  # Display preds. Accepts all YOLO predict arguments

        # Estrai informazioni dai risultati YOLO
        boxes = results[0].boxes.xyxy.numpy()  # Converti tensori in numpy per una manipolazione più semplice
        classes = results[0].boxes.cls.numpy()  # Aggiungi questa linea per le classi
        confidences = results[0].boxes.conf.numpy()  # Aggiungi questa linea per le confidenze

        # Combina le informazioni in una singola lista per ogni box
        response_dict = {"boxes": boxes, "classes": classes, "confidences": confidences}
        print("BOXES RESULT", boxes)
        print("CLASSES RESULT", classes)
        print("CONFIDENCES RESULT", confidences)
        number_something_strange_detected = 0
        for index in range(len(response_dict["boxes"])):
            current_confidence = float(response_dict["confidences"][index])
            if current_confidence < 0.5:
                # print("SKIPPED" +str(current_confidence))
                continue
            if int(response_dict["classes"][index] != 2) and int(response_dict["classes"][index] != 5):
                number_something_strange_detected += 1
            print("BOX" + str(current_confidence))
            x1 = int(response_dict["boxes"][index][0])
            x2 = int(response_dict["boxes"][index][2])
            y1 = int(response_dict["boxes"][index][1])
            y2 = int(response_dict["boxes"][index][3])

            # Start coordinate, here (5, 5)
            # represents the top left corner of rectangle
            start_point = (x1, y1)

            # Ending coordinate, here (220, 220)
            # represents the bottom right corner of rectangle
            end_point = (x2, y2)

            # Blue color in BGR
            color = (255, 0, 0)

            # Line thickness of 2 px
            thickness = 2

            # Using cv2.rectangle() method
            # Draw a rectangle with blue line borders of thickness of 2 px
            frame = cv2.rectangle(frame, start_point, end_point, color, thickness)
        log_folder = STREAM_PATH_OK
        log_folder_txt = STREAM_PATH_OK + "_TXT"

        if (number_something_strange_detected > 0):
            log_folder = STREAM_PATH_NOK
            log_folder_txt = STREAM_PATH_NOK + "_TXT"
        # print("YOLO DETECTION",response)
        # Check for successful response
        # response.raise_for_status()

        # Print inference results
        # print(json.dumps(response.json(), indent=2))
        # cv2.imshow('Capturing', frame)
        time.sleep(0.5)
        now_string = str(datetime.now()).replace(":", ".")
        cv2.imwrite(log_folder + "/" + now_string.replace(":", ".") + ".png", frame)
        with open(log_folder_txt + "/" + now_string.replace(":", ".") + ".txt", "w") as outfile:
            outfile.write(str(boxes) + "\n" + str(classes) + "\n" + str(confidences))  # if cv2.waitKey(1) & 0xFF == ord('q'):  # click q to stop capturing  #    break

    cap.release()
    cv2.destroyAllWindows()
    return 0'''


if __name__ == '__main__':
    now_string = str(datetime.now()).replace(":", ".")
    print("**********SYSTEM STARTED AT "+now_string+"**********")
    import sys
    create_main_cam_folder(BASE_SYSTEM_FOLDER)
    sys.exit(main(sys.argv))
