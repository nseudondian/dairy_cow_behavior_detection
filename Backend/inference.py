"""copy of inference for final submission for fixing bugs"""
import os
import cv2
import time
import csv
import numpy as np
import random
from PIL import Image
from ultralytics import YOLO
from classificationmodel import CowIdentificationModel
from deep_sort_realtime.deepsort_tracker import DeepSort
from torchvision.transforms import transforms
from utils import convert_to_top_left_v1, calculate_centroid, calculate_centroid_distance, are_boxes_overlapping
from database import Database
import torch
import subprocess

root_dir = 'static'
temp_folder = 'temp'
annotated_folder = 'annotated_video'

class Inference:
    def is_point_near_body(self, point, body_box, buffer=10):
        x, y = point
        x1, y1, x2, y2 = body_box
        return x1 - buffer <= x <= x2 + buffer and y1 - buffer <= y <= y2 + buffer

    def is_inside(self, small_box, big_box):
        x1s, y1s, x2s, y2s = small_box
        x1b, y1b, x2b, y2b = big_box
        return x1s >= x1b and y1s >= y1b and x2s <= x2b and y2s <= y2b

    def __init__(self, video_path, output_path=None, model_path='Backend/models/yolov8/last_trained_best.pt'):
        self.video_path = video_path
        filename = os.path.basename(video_path)

        if output_path is None:
            output_path = os.path.join('static', 'annotated_video', f"{os.path.splitext(filename)[0]}.mp4")

        if not output_path.endswith('.mp4'):
            output_path += '.mp4'

        self.output_path = output_path
        print(" Using input video:", self.video_path)
        print(" Saving annotated video to:", self.output_path)
        self.model = YOLO(model_path)
        self.tracker = DeepSort(max_age=30)
        self.db = Database()
        self.fps = 30
        self.logged_brushing = set()
        self.logged_drinking = set()
        self.logged_headbutts = set()

        if not output_path.endswith('.mp4'):
            output_path += '.mp4'
        self.output_path = output_path
        print(" Saving annotated video to:", self.output_path)




        self.classifier = CowIdentificationModel()
        self.classifier.load_state_dict(torch.load("Backend/models/classifier/best_model.pth", map_location="cpu"))
        self.classifier.eval()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.track_to_cnn_id = {}

        self.BRUSHING_DISTANCE_THRESHOLD = 160
        self.OVERLAP_THRESHOLD = 0.05
        self.DRINKING_MIN_FRAMES = 75
        self.HEAD_DISTANCE = 10
        self.MIN_NUDGE_SPEED = 0.15
        self.DOT_PRODUCT_MIN = 0

        self.headbutt_log = []
        self.brushing_states = {}
        self.drinking_states = {}

    def predict_cow_id(self, image):
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        image_tensor = self.transform(image).unsqueeze(0)
        with torch.no_grad():
            output = self.classifier(image_tensor)
            probabilities = torch.nn.functional.softmax(output, dim=1)
            _, predicted = torch.max(probabilities, 1)
        return int(predicted.item())

    def inference(self):
        self.db.delete_existing_events_for_video(self.video_path)
        print(" Starting inference...")
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f" Failed to open video: {self.video_path}")
            return
        
        filename = os.path.basename(self.video_path)
        date_str = filename[5:13]
        time_str = filename[13:19]
        cam_str = filename[19:22] if len(filename) >= 22 else '000'
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        print(f" Frame width: {frame_w}, height: {frame_h}")
        print(f" FPS: {self.fps}")
        print(f" Output path: {self.output_path}")

        out_vid = cv2.VideoWriter(self.output_path, fourcc, self.fps, (frame_w, frame_h))

        if not out_vid.isOpened():
            print(f"Failed to open VideoWriter for path: {self.output_path}")
            return
        else:
            print(f"VideoWriter initialized. Output will be saved to: {self.output_path}")



        old_head_positions = {}
        recent_hits = {}
        frame_idx = 0
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
                
            print(f" Inference completed. Total frames processed: {frame_count}")
            results = self.model.track(frame, conf=0.3, tracker="bytetrack.yaml")
            if not results or len(results[0].boxes) == 0:
                out_vid.write(frame)
                frame_idx += 1
                continue

            boxes = results[0].boxes
            ids = boxes.id.cpu().numpy().astype(int)
            xyxys = boxes.xyxy.cpu().numpy().astype(int)
            classes = boxes.cls.cpu().numpy().astype(int)
            scores = boxes.conf.cpu().numpy()

            cow_boxes = []
            head_boxes = []
            brush_boxes = []
            tub_boxes = []

            for i in range(len(ids)):
                cls = classes[i]
                bbox = xyxys[i]
                tid = ids[i]

                if cls == 0:
                    brush_boxes.append(bbox)
                elif cls == 1:
                    cow_boxes.append((tid, bbox))
                elif cls == 2 and scores[i] > 0.5:
                    head_boxes.append((tid, bbox))
                elif cls == 3:
                    tub_boxes.append(bbox)

            for _, head_box in head_boxes:
                cv2.rectangle(frame, (head_box[0], head_box[1]), (head_box[2], head_box[3]), (255, 255, 102), 2)
                cv2.putText(frame, "Cow Head", (head_box[0], head_box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 102), 2)
            for brush_box in brush_boxes:
                cv2.rectangle(frame, (brush_box[0], brush_box[1]), (brush_box[2], brush_box[3]), (255, 0, 0), 2)
                cv2.putText(frame, "Brush", (brush_box[0], brush_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            for tid, bbox in cow_boxes:
                cow_img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                if cow_img.size != 0:
                    cnn_id = self.predict_cow_id(cow_img)
                    self.track_to_cnn_id[tid] = cnn_id
                    label = f"cow - {tid}"
                    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                    cv2.putText(frame, label, (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

#             # Brushing detection logic 
            for tid, cow_box in cow_boxes:
                cow_centroid = calculate_centroid(cow_box)
                is_brushing = any(
                    calculate_centroid_distance(cow_centroid, calculate_centroid(brush)) < self.BRUSHING_DISTANCE_THRESHOLD or
                    are_boxes_overlapping(cow_box, brush)[0]
                    for brush in brush_boxes
                )
                if tid not in self.brushing_states:
                    self.brushing_states[tid] = {'active': False, 'start_frame': None}
                state = self.brushing_states[tid]
                if is_brushing:
                    if not state['active']:
                        state['active'] = True
                        state['start_frame'] = frame_idx
                    brushing_duration = (frame_idx - state['start_frame']) / self.fps
                    cv2.putText(frame, f"Brushing", (cow_box[0], cow_box[1]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                elif state['active']:
                    brushing_duration = (frame_idx - state['start_frame']) / self.fps

                    if brushing_duration >= 1.0 and frame_idx % 50 == 0:
                        clean_tid = str(int(tid))
                        event_key = f"{clean_tid}_{state['start_frame']}"

                        if event_key not in self.logged_brushing:
                            self.db.insert_cow_events_data(
                                clean_tid,
                                'Brushing',
                                round(brushing_duration, 2),
                                os.path.basename(self.video_path),
                                date_str,
                                time_str,
                                cam_str,
                                round(brushing_duration, 2),
                                None
                            )
                            self.logged_brushing.add(event_key)
                
                    state['active'] = False

            # Drinking detection
            for tid, cow_box in cow_boxes:
                head_box = cow_box
                for _, hbox in head_boxes:
                    if self.is_inside(hbox, cow_box):
                        head_box = hbox
                        break
                threshold = 0.15 if not np.array_equal(head_box, cow_box) else 0.05
                drinking_near = False
                for tub in tub_boxes:
                    overlap, area = are_boxes_overlapping(head_box, tub)
                    if overlap and area > threshold:
                        drinking_near = True
                        cv2.rectangle(frame, (tub[0], tub[1]), (tub[2], tub[3]), (0, 255, 255), 2)
                        cv2.putText(frame, "Water Tub", (tub[0], tub[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                if tid not in self.drinking_states:
                    self.drinking_states[tid] = {'active': False, 'start_frame': None}
                state = self.drinking_states[tid]
                if drinking_near:
                    if not state['active']:
                        state['active'] = True
                        state['start_frame'] = frame_idx
                    drinking_duration = (frame_idx - state['start_frame']) / self.fps
                    cv2.putText(frame, f"Drinking", (cow_box[0], cow_box[1]-50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.rectangle(frame, (cow_box[0], cow_box[1]), (cow_box[2], cow_box[3]), (255, 255, 0), 2)
                elif state['active']:
                    drinking_duration = (frame_idx - state['start_frame']) / self.fps

                    if drinking_duration >= 1.0 and frame_idx % 50 == 0:
                        clean_tid = str(int(tid))
                        event_key = f"{clean_tid}_{state['start_frame']}"

                        if event_key not in self.logged_drinking:
                            self.db.insert_cow_events_data(
                                clean_tid,
                                'Drinking',
                                round(drinking_duration, 2),
                                os.path.basename(self.video_path),
                                date_str,
                                time_str,
                                cam_str,
                                round(drinking_duration, 2),
                                None
                            )
                            self.logged_drinking.add(event_key)
                 
                    state['active'] = False

            # Headbutt detection
            current_cows = []
            velocities = {}
            matched_heads = {}

            for cow_id, cow_box in cow_boxes:
                matched = False
                for head_id, head_box in head_boxes:
                    if self.is_inside(head_box, cow_box):
                        hx = (head_box[0] + head_box[2]) // 2
                        hy = (head_box[1] + head_box[3]) // 2
                        headpt = (hx, hy)
                        matched_heads[cow_id] = headpt
                        matched = True

                        if cow_id in old_head_positions:
                            vx = headpt[0] - old_head_positions[cow_id][0]
                            vy = headpt[1] - old_head_positions[cow_id][1]
                        else:
                            vx, vy = 0, 0

                        speed = np.sqrt(vx ** 2 + vy ** 2)
                        velocities[cow_id] = (vx, vy, speed)
                        old_head_positions[cow_id] = headpt

                        current_cows.append((cow_id, cow_box, headpt))
                        break
                if not matched:
                    continue

            pairs_this_frame = []
            for i in range(len(current_cows)):
                for j in range(i + 1, len(current_cows)):
                    idA, boxA, headA = current_cows[i]
                    idB, boxB, headB = current_cows[j]

                    (vxA, vyA, spA) = velocities[idA]
                    cxB = (boxB[0] + boxB[2]) // 2
                    cyB = (boxB[1] + boxB[3]) // 2
                    dx = cxB - headA[0]
                    dy = cyB - headA[1]
                    dotA = vxA * dx + vyA * dy
                    closeA = self.is_point_near_body(headA, boxB, buffer=self.HEAD_DISTANCE)

                    (vxB, vyB, spB) = velocities[idB]
                    cxA = (boxA[0] + boxA[2]) // 2
                    cyA = (boxA[1] + boxA[3]) // 2
                    dxB = cxA - headB[0]
                    dyB = cyA - headB[1]
                    dotB = vxB * dxB + vyB * dyB
                    closeB = self.is_point_near_body(headB, boxA, buffer=self.HEAD_DISTANCE)

                    pair_key = tuple(sorted((idA, idB)))
                    headbutt_A = closeA and spA >= self.MIN_NUDGE_SPEED and dotA > self.DOT_PRODUCT_MIN
                    headbutt_B = closeB and spB >= self.MIN_NUDGE_SPEED and dotB > self.DOT_PRODUCT_MIN

                    cnn_id_A = self.track_to_cnn_id.get(idA, idA)
                    cnn_id_B = self.track_to_cnn_id.get(idB, idB)
                    cnn_pair_key = tuple(sorted((cnn_id_A, cnn_id_B)))

                    if (headbutt_A or headbutt_B) and cnn_pair_key not in self.logged_headbutts:
                        time_s = round(frame_idx / self.fps, 2)
                        self.headbutt_log.append({
                            "cow_1": cnn_id_A,
                            "cow_2": cnn_id_B,
                            "time": time_s,
                            "video_name": filename,
                            "video_date": date_str,
                            "video_time": time_str,
                            "camera": cam_str
                        })
                        headbutt_pair_id = f"{idA}-{idB}"
                        self.db.insert_cow_events_data(
                            headbutt_pair_id,
                            'Headbutt',
                            time_s,
                            os.path.basename(self.video_path),
                            date_str,
                            time_str,
                            cam_str,
                            None,
                            time_s
                        )
                        self.logged_headbutts.add(cnn_pair_key)
                        pairs_this_frame.append(((idA, boxA, headA), (idB, boxB, headB), time_s))
                        # Highlight both cows involved in headbutt
                        cv2.rectangle(frame, (boxA[0], boxA[1]), (boxA[2], boxA[3]), (0, 0, 255), 2)
                        cv2.rectangle(frame, (boxB[0], boxB[1]), (boxB[2], boxB[3]), (0, 0, 255), 2)
                        cv2.putText(frame, f"Headbutt", (boxA[0], boxA[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(frame, f"Headbutt", (boxB[0], boxB[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        print(f" Detected headbutt between {idA} and {idB} at {time_s}s")


            out_vid.write(frame) 
            frame_idx += 1
            frame_count += 1

        cap.release()
        out_vid.release()
        print(f"Opened video: {self.video_path}")

        def fix_video_for_browser(original_path):
            # Create a fixed output path
            fixed_path = original_path.replace('.mp4', '_fixed.mp4')
            
            # Run ffmpeg to re-encode
            cmd = [
                'ffmpeg', '-y', 
                '-i', original_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-movflags', '+faststart',
                fixed_path
            ]
            
            try:
                subprocess.run(cmd, check=True)
                print(f"Video fixed and saved to: {fixed_path}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to fix video: {e}")

        fix_video_for_browser(self.output_path)

        with open("headbutt_events.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["cow_1", "cow_2", "time", "video_name", "video_date", "video_time", "camera"])
            writer.writeheader()
            for event in self.headbutt_log:
                writer.writerow({
                    "cow_1": event["cow_1"],
                    "cow_2": event["cow_2"],
                    "time": event["time"],  
                    "video_name": event["video_name"],
                    "video_date": event["video_date"],
                    "video_time": event["video_time"],
                    "camera": event["camera"]
                })
    


        print(" Inference complete, video annotated, and headbutts saved to CSV and DB.")

if __name__ == "__main__":
    video_path = r"Backend\\no_individual_tracking\\Event20240626151811002.mp4"
    output_path = "static/output_video/sample_output_mergers.mp4"
    Inference(video_path, output_path).inference()


