from picamera2 import Picamera2
import cv2
from ultralytics import YOLO
import sqlite3
import datetime
import db1000

conn, cursor = db1000.db_setup() # create db

#cam set up
yolo = YOLO("yolo26n.pt")
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (1080, 640)})
picam2.configure(config)
picam2.start()
picam2.video_configuration.controls.FrameRate = 25

# vars
line_x = 360
line_y = 720
left_to_right_count = 0
right_to_left_count = 0
crossing_state = {} # dictionary to store state of each id, "entered_zone_left" or "entered_zone_right"
current_state = {}
conf = 0.80

# make the camera work lol
while True:
    frame = picam2.capture_array()

    #red line (counting line)
    cv2.line(frame, (line_x, 0), (line_x, frame.shape[0]), (0, 0, 255), 2)
    cv2.line(frame, (line_y, 0), (line_y, frame.shape[0]), (0, 0, 255), 2) # failed experiment (works somewhat but conflicting mechanism & hardware limitation)

    results = yolo.track(
        frame,
        persist=True, # live feed
        tracker="bytetrack.yaml",
        classes=[0], # only detect ppl
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
            cx = (x1 + x2) // 2                   # centre of the bounding box

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
                    print("IN ______________________________________________----------------")
                    left_to_right_count += 1
                    direction = "in"
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    cursor.execute(
                        "INSERT INTO Detections (timeStamp,direction) VALUES (?,?)",
                        (timestamp,direction)
                    )
                    conn.commit()
                    
                    # Mark as counted so they don't trigger again
                    crossing_state[track_id] = "counted"
                


                # started on the right and just crossed the line = "OUT"
                elif current_state[track_id] == "from_right" and cx <= line_x:
                    print("OUT7_____________________________________________")
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

    cv2.putText(frame, f"In: {left_to_right_count}  Out: {right_to_left_count}",
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
#cv2.destroyAllWindows()
conn.close()
