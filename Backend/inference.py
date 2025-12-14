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
        
        # Brush motion tracking for filtering false positives
        self.brush_motion_history = {}
        self.MOTION_HISTORY_LENGTH = 10
        self.MOTION_THRESHOLD = 2.0




        self.classifier = CowIdentificationModel()
        self.classifier.load_state_dict(torch.load("Backend/models/classifier/best_model.pth", map_location="cpu"))
        self.classifier.eval()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.track_to_cnn_id = {}

        # Updated thresholds based on latest calibration
        self.BRUSHING_DISTANCE_THRESHOLD = 80  # More accurate detection
        self.OVERLAP_THRESHOLD = 0.02  # Reduced from 0.05
        self.DRINKING_MIN_FRAMES = 30  # More sensitive detection
        self.DRINKING_OVERLAP_THRESHOLD_HEAD = 0.05
        self.DRINKING_OVERLAP_THRESHOLD_COW = 0.03
        self.HEAD_DISTANCE = 10
        self.MIN_NUDGE_SPEED = 0.15
        self.DOT_PRODUCT_MIN = 0
        
        # Event merging parameters
        self.MERGE_EVENT_WITHIN_SECONDS = 5.0  # Merge if restart within 5 secs
        self.FINALIZE_EVENT_AFTER_SECONDS = 5.0  # Log event if no activity for 5 secs

        self.headbutt_log = []
        # New event state tracking with merging support
        self.brushing_states = {}  # Will store: merged_event_start_frame, last_active_segment_end_frame, is_active_in_previous_frame
        self.drinking_states = {}  # Same structure as brushing_states

    def is_brush_moving(self, brush_id):
        """Check if brush is actually moving to filter false positives"""
        history = self.brush_motion_history.get(brush_id, [])
        if len(history) < 2:
            return False
        total_dist = sum(calculate_centroid_distance(history[i-1], history[i]) for i in range(1, len(history)))
        if len(history) > 1:
            avg_dist = total_dist / (len(history) - 1)
            return avg_dist > self.MOTION_THRESHOLD
        return False
    
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
        
        # Calculate frame thresholds for event merging
        MERGE_THRESHOLD_FRAMES = int(self.MERGE_EVENT_WITHIN_SECONDS * self.fps)
        FINALIZE_EVENT_GAP_FRAMES = int(self.FINALIZE_EVENT_AFTER_SECONDS * self.fps)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
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
                    brush_boxes.append((tid, bbox))
                    # Update brush motion history
                    centroid = calculate_centroid(bbox)
                    history = self.brush_motion_history.setdefault(tid, [])
                    history.append(centroid)
                    if len(history) > self.MOTION_HISTORY_LENGTH:
                        history.pop(0)
                elif cls == 1:
                    cow_boxes.append((tid, bbox))
                elif cls == 2 and scores[i] > 0.5:
                    head_boxes.append((tid, bbox))
                elif cls == 3:
                    tub_boxes.append(bbox)

            for _, head_box in head_boxes:
                cv2.rectangle(frame, (head_box[0], head_box[1]), (head_box[2], head_box[3]), (255, 255, 102), 2)
                cv2.putText(frame, "Cow Head", (head_box[0], head_box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 102), 2)
            for _, brush_box in brush_boxes:
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

            # Brushing detection with motion filtering and event merging
            brushing_cows_current_frame = set()
            for tid, cow_box in cow_boxes:
                cow_centroid = calculate_centroid(cow_box)
                # Check if cow is near a moving brush
                is_brushing = False
                for brush_tid, brush in brush_boxes:
                    brush_moving = self.is_brush_moving(brush_tid)
                    distance_close = calculate_centroid_distance(cow_centroid, calculate_centroid(brush)) < self.BRUSHING_DISTANCE_THRESHOLD
                    overlap, area = are_boxes_overlapping(cow_box, brush)
                    overlap_sufficient = overlap and area > self.OVERLAP_THRESHOLD
                    
                    if (distance_close or overlap_sufficient) and brush_moving:
                        is_brushing = True
                        break
                
                if is_brushing:
                    brushing_cows_current_frame.add(tid)
                    cv2.putText(frame, f"Brushing", (cow_box[0], cow_box[1]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
            # Update brushing states with event merging logic
            all_known_cow_ids = set(self.brushing_states.keys()).union([tid for tid, _ in cow_boxes])
            for cow_id in all_known_cow_ids:
                is_brushing_now = cow_id in brushing_cows_current_frame
                
                if cow_id not in self.brushing_states:
                    self.brushing_states[cow_id] = {
                        'merged_event_start_frame': None,
                        'last_active_segment_end_frame': None,
                        'is_active_in_previous_frame': False
                    }
                
                state = self.brushing_states[cow_id]
                
                if is_brushing_now:
                    if not state['is_active_in_previous_frame']:
                        # Starting or restarting brushing
                        if state['merged_event_start_frame'] is None:
                            # Brand new event
                            state['merged_event_start_frame'] = frame_idx
                        elif state['last_active_segment_end_frame'] is not None:
                            # Check if we should merge or start new event
                            gap_frames = frame_idx - state['last_active_segment_end_frame'] - 1
                            if gap_frames > MERGE_THRESHOLD_FRAMES:
                                # Gap too large, finalize old event and start new
                                duration_seconds = (state['last_active_segment_end_frame'] - state['merged_event_start_frame'] + 1) / self.fps
                                if duration_seconds >= 1.0:
                                    clean_tid = str(int(cow_id))
                                    event_key = f"{clean_tid}_{state['merged_event_start_frame']}"
                                    if event_key not in self.logged_brushing:
                                        self.db.insert_cow_events_data(
                                            clean_tid, 'Brushing', round(duration_seconds, 2),
                                            os.path.basename(self.video_path), date_str, time_str, cam_str,
                                            round(duration_seconds, 2), None
                                        )
                                        self.logged_brushing.add(event_key)
                                state['merged_event_start_frame'] = frame_idx
                    
                    state['is_active_in_previous_frame'] = True
                    state['last_active_segment_end_frame'] = frame_idx
                else:
                    # Not brushing this frame
                    state['is_active_in_previous_frame'] = False
                    
                    # Check if we should finalize the event
                    if state['merged_event_start_frame'] is not None and state['last_active_segment_end_frame'] is not None:
                        gap_frames = frame_idx - state['last_active_segment_end_frame'] - 1
                        if gap_frames > FINALIZE_EVENT_GAP_FRAMES:
                            # Finalize the event
                            duration_seconds = (state['last_active_segment_end_frame'] - state['merged_event_start_frame'] + 1) / self.fps
                            if duration_seconds >= 1.0:
                                clean_tid = str(int(cow_id))
                                event_key = f"{clean_tid}_{state['merged_event_start_frame']}"
                                if event_key not in self.logged_brushing:
                                    self.db.insert_cow_events_data(
                                        clean_tid, 'Brushing', round(duration_seconds, 2),
                                        os.path.basename(self.video_path), date_str, time_str, cam_str,
                                        round(duration_seconds, 2), None
                                    )
                                    self.logged_brushing.add(event_key)
                            state['merged_event_start_frame'] = None

            # Drinking detection with improved thresholds and event merging
            drinking_cows_current_frame = set()
            for tid, cow_box in cow_boxes:
                # Find matching head if available
                head_box = None
                for _, hbox in head_boxes:
                    if self.is_inside(hbox, cow_box):
                        head_box = hbox
                        break
                
                # Use improved thresholds
                det_box = head_box if head_box is not None else cow_box
                threshold = self.DRINKING_OVERLAP_THRESHOLD_HEAD if head_box is not None else self.DRINKING_OVERLAP_THRESHOLD_COW
                
                drinking_near = False
                for tub in tub_boxes:
                    overlap, area = are_boxes_overlapping(det_box, tub)
                    if overlap and area > threshold:
                        drinking_near = True
                        cv2.rectangle(frame, (tub[0], tub[1]), (tub[2], tub[3]), (0, 255, 255), 2)
                        cv2.putText(frame, "Water Tub", (tub[0], tub[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                        break
                
                if drinking_near:
                    drinking_cows_current_frame.add(tid)
                    cv2.putText(frame, f"Drinking", (cow_box[0], cow_box[1]-50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.rectangle(frame, (cow_box[0], cow_box[1]), (cow_box[2], cow_box[3]), (255, 255, 0), 2)
            
            # Update drinking states with event merging logic
            all_known_cow_ids_drinking = set(self.drinking_states.keys()).union([tid for tid, _ in cow_boxes])
            for cow_id in all_known_cow_ids_drinking:
                is_drinking_now = cow_id in drinking_cows_current_frame
                
                if cow_id not in self.drinking_states:
                    self.drinking_states[cow_id] = {
                        'merged_event_start_frame': None,
                        'last_active_segment_end_frame': None,
                        'is_active_in_previous_frame': False
                    }
                
                d_state = self.drinking_states[cow_id]
                
                if is_drinking_now:
                    if not d_state['is_active_in_previous_frame']:
                        # Starting or restarting drinking
                        if d_state['merged_event_start_frame'] is None:
                            # Brand new event
                            d_state['merged_event_start_frame'] = frame_idx
                        elif d_state['last_active_segment_end_frame'] is not None:
                            # Check if we should merge or start new event
                            gap_frames = frame_idx - d_state['last_active_segment_end_frame'] - 1
                            if gap_frames > MERGE_THRESHOLD_FRAMES:
                                # Gap too large, finalize old event and start new
                                duration_frames = d_state['last_active_segment_end_frame'] - d_state['merged_event_start_frame'] + 1
                                if duration_frames >= self.DRINKING_MIN_FRAMES:
                                    duration_seconds = duration_frames / self.fps
                                    clean_tid = str(int(cow_id))
                                    event_key = f"{clean_tid}_{d_state['merged_event_start_frame']}"
                                    if event_key not in self.logged_drinking:
                                        self.db.insert_cow_events_data(
                                            clean_tid, 'Drinking', round(duration_seconds, 2),
                                            os.path.basename(self.video_path), date_str, time_str, cam_str,
                                            round(duration_seconds, 2), None
                                        )
                                        self.logged_drinking.add(event_key)
                                d_state['merged_event_start_frame'] = frame_idx
                    
                    d_state['is_active_in_previous_frame'] = True
                    d_state['last_active_segment_end_frame'] = frame_idx
                else:
                    # Not drinking this frame
                    d_state['is_active_in_previous_frame'] = False
                    
                    # Check if we should finalize the event
                    if d_state['merged_event_start_frame'] is not None and d_state['last_active_segment_end_frame'] is not None:
                        gap_frames = frame_idx - d_state['last_active_segment_end_frame'] - 1
                        if gap_frames > FINALIZE_EVENT_GAP_FRAMES:
                            # Finalize the event
                            duration_frames = d_state['last_active_segment_end_frame'] - d_state['merged_event_start_frame'] + 1
                            if duration_frames >= self.DRINKING_MIN_FRAMES:
                                duration_seconds = duration_frames / self.fps
                                clean_tid = str(int(cow_id))
                                event_key = f"{clean_tid}_{d_state['merged_event_start_frame']}"
                                if event_key not in self.logged_drinking:
                                    self.db.insert_cow_events_data(
                                        clean_tid, 'Drinking', round(duration_seconds, 2),
                                        os.path.basename(self.video_path), date_str, time_str, cam_str,
                                        round(duration_seconds, 2), None
                                    )
                                    self.logged_drinking.add(event_key)
                            d_state['merged_event_start_frame'] = None

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

        # Finalize any remaining events at end of video
        for cow_id, state in self.brushing_states.items():
            if state['merged_event_start_frame'] is not None and state['last_active_segment_end_frame'] is not None:
                duration_seconds = (state['last_active_segment_end_frame'] - state['merged_event_start_frame'] + 1) / self.fps
                if duration_seconds >= 1.0:
                    clean_tid = str(int(cow_id))
                    event_key = f"{clean_tid}_{state['merged_event_start_frame']}"
                    if event_key not in self.logged_brushing:
                        self.db.insert_cow_events_data(
                            clean_tid, 'Brushing', round(duration_seconds, 2),
                            os.path.basename(self.video_path), date_str, time_str, cam_str,
                            round(duration_seconds, 2), None
                        )
                        self.logged_brushing.add(event_key)
        
        for cow_id, d_state in self.drinking_states.items():
            if d_state['merged_event_start_frame'] is not None and d_state['last_active_segment_end_frame'] is not None:
                duration_frames = d_state['last_active_segment_end_frame'] - d_state['merged_event_start_frame'] + 1
                if duration_frames >= self.DRINKING_MIN_FRAMES:
                    duration_seconds = duration_frames / self.fps
                    clean_tid = str(int(cow_id))
                    event_key = f"{clean_tid}_{d_state['merged_event_start_frame']}"
                    if event_key not in self.logged_drinking:
                        self.db.insert_cow_events_data(
                            clean_tid, 'Drinking', round(duration_seconds, 2),
                            os.path.basename(self.video_path), date_str, time_str, cam_str,
                            round(duration_seconds, 2), None
                        )
                        self.logged_drinking.add(event_key)
        
        cap.release()
        out_vid.release()
        print(f"Opened video: {self.video_path}")
        print(f" Inference completed. Total frames processed: {frame_count}")

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


