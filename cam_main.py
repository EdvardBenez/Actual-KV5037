from picamera2 import Picamera2
import cv2
from ultralytics import YOLO
import sqlite3
import datetime
import db_main #database file

conn, cursor = db_main.db_setup() # create db

#cam set up & yolo version
yolo = YOLO("yolo26n.pt")
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (1080, 640)})#sets cam resolution and RGB
picam2.configure(config)
picam2.start()
picam2.video_configuration.controls.FrameRate = 25 #set frame rate

# variables
line_x = 360 # virtual line 1
line_y = 720 #virtual line 2
left_to_right_count = 0
right_to_left_count = 0
crossing_state = {} # dictionary to store state of each id, "entered_zone_left" or "entered_zone_right"
current_state = {}
conf = 0.80 #how critical is it for saying somthing is a person

# Camera loop
while True:
    frame = picam2.capture_array()#image from camera to be read

    #red line (counting line)
    cv2.line(frame, (line_x, 0), (line_x, frame.shape[0]), (0, 0, 255), 2)#Out line
    cv2.line(frame, (line_y, 0), (line_y, frame.shape[0]), (0, 0, 255), 2)#In line
	#yolo attributes
    results = yolo.track(
        frame,
        persist=True, # live feed
        tracker="bytetrack.yaml",
        classes=[0], # set yolo to only detect ppl
        verbose=False # disbale terminal flooding
    )

    result = results[0]

    if result.boxes is not None:
        for box in result.boxes:
            if box.id is None:
                continue

            #calculating value of body centre for position tracking
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            track_id = int(box.id[0])
            cx = (x1 + x2) // 2                   # centre of a persons' bounding box

            # LINE CROSSING LOGIC
            
            # Determining the crossing state
            if track_id not in crossing_state:
                if cx <= line_y:
                    crossing_state[track_id] = "from_left"
                elif cx >= line_x:
                    crossing_state[track_id] = "from_right"

            else:
                current_state[track_id] = crossing_state[track_id]
                # started on the left and just crossed the line = "IN"
                if current_state[track_id] == "from_left" and cx >= line_y:
                    print("IN ______________________________________________----------------")#shows on termnial for testing
                    left_to_right_count += 1
                    direction = "in"
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    cursor.execute(
                        "INSERT INTO Detections (timeStamp,direction) VALUES (?,?)",
                        (timestamp,direction)
                    )#updates the database
                    conn.commit()
                    
                    # Mark as counted so they don't trigger again
                    crossing_state[track_id] = "counted"
                


                # started on the right and just crossed the line = "OUT"
                elif current_state[track_id] == "from_right" and cx <= line_x:
                    print("OUT7_____________________________________________")#for debugging/testing
                    right_to_left_count += 1
                    direction = "out"
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    cursor.execute(
                        "INSERT INTO Detections (timeStamp,direction) VALUES (?,?)",
                        (timestamp,direction)
                    )
                    conn.commit()
                    
                    crossing_state[track_id] = "counted"
                    #print(f"[{timestamp}] Person {track_id} exited. Total out: {right_to_left_count}")

            #green box (bounding box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{track_id}",
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"In: {left_to_right_count}  Out: {right_to_left_count}",     #in & out count on window
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

    #cv2.imshow("Frame", frame)       # comment this out for disabling windows

    #if cv2.waitKey(1) == ord('q'):   # comment this out for disabling windows
        #break                        # comment this out for disabling windows

picam2.stop()
#cv2.destroyAllWindows()              # comment this out for disabling windows
conn.close()
