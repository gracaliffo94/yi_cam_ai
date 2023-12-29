from PIL import Image
from ultralytics import YOLO
import os
import time
from datetime import datetime

BASE_SYSTEM_FOLDER = "CamSystem"
model = YOLO("./yolov8n.pt")
DELETE_FILE = True
append_string = ""
if not DELETE_FILE:
    append_string = "_pred"


def create_prediction_dirs_ifne(directory_name):
    # str just to be sure
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
    else:
        None

def consume_files_in_folder(folder_path):
    device_images_paths = [f for f in os.listdir(folder_path) if os.path.isdir(folder_path+"/"+f)]
    print(device_images_paths)

    for device_images_path in device_images_paths:
        current_stream_path = BASE_SYSTEM_FOLDER + "/" + device_images_path + "/Stream"
        images_stream_paths = [current_stream_path+"/"+f for f in os.listdir(current_stream_path) if os.path.isfile(current_stream_path+"/"+f)]
        folder_predictions = BASE_SYSTEM_FOLDER + "/" + device_images_path + "/Predicted"
        folder_predictions_txt = folder_predictions + "_txt"
        create_prediction_dirs_ifne(folder_predictions)
        create_prediction_dirs_ifne(folder_predictions_txt)

        # Dopo aver preso la lista di tutti i file correnti nella folder, aspettiamo 1 secondo che sennò crasha perchè yolo non li trova ancora
        time.sleep(1)
        for file_path in images_stream_paths:
            print("Analyzing ",file_path)
            start_time = time.time()
            results = model.predict(source=file_path)  # Display preds. Accepts all YOLO predict arguments

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
            now_string = str(datetime.now()).replace(":", ".")
            with open(folder_predictions_txt + "/" + now_string + ".txt", "w") as outfile:
                outfile.write(str(boxes) + "\n" + str(classes) + "\n" + str(confidences))
            # Show the results
            for r in results:
                im_array = r.plot()  # plot a BGR numpy array of predictions
                im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
                if DELETE_FILE:
                    os.remove(file_path)
                im.save(folder_predictions + "/" + file_path.split("/")[-1])  # save image

print("Started!",os.listdir(BASE_SYSTEM_FOLDER))
current_iteration = 0
while True:
    current_iteration += 1
    print("[Iteration " + str(current_iteration) + "]")
    consume_files_in_folder(BASE_SYSTEM_FOLDER)