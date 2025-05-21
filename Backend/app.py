from flask import Flask, request, jsonify, redirect, url_for
import os
import subprocess
import pandas as pd
import uuid
from inference import Inference 
from database import Database
from PIL import Image
from flask_cors import CORS
import pytz
from datetime import datetime
from flask import send_from_directory


# app = Flask(__name__, static_url_path='/static', static_folder='static')
# CORS(app)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_url_path='/static', static_folder=STATIC_FOLDER)
CORS(app)

db = Database()

root_dir = 'static'
UPLOAD_FOLDER = os.path.join(root_dir, 'input_video')
temp_folder = os.path.join(root_dir, 'temp')
annotated_folder = os.path.join(root_dir, 'annotated_video')


os.makedirs(temp_folder, exist_ok=True)
os.makedirs(annotated_folder, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return jsonify(message='Welcome to the API')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files or request.files['file'].filename == '':
            return jsonify(message="No 'file' provided or selected")

        file = request.files['file']
        original_filename = file.filename.strip()

        if not original_filename.endswith('.mp4'):
            return jsonify(message="Only .mp4 files are supported")

        save_path = os.path.join(temp_folder, original_filename)
        file.save(save_path)

        # Save to DB with filename
        db.insert_cow_Video_Infomation_data(input_video=original_filename.replace('.mp4', ''))

        # return jsonify
        return jsonify(
            message='File uploaded successfully',
            type='success',
            filename=save_path
        )

    except Exception as e:
        return jsonify(message=f'Error: {str(e)}'), 500



@app.route('/start_inference', methods=['POST'])
def start_inference():
    if 'video_name' not in request.form or request.form['video_name'] == '':
        return jsonify(message='Please Provide The video_name to test.')

    filename = request.form['video_name']
    print(f"Requested video: {filename}")

    try:
        video_path = os.path.join(root_dir, filename)
        video_path = os.path.normpath(video_path)

        output_path = os.path.join(annotated_folder, os.path.basename(filename))
        print(f"Output will be saved to: {output_path}")

        inf = Inference(video_path, output_path)
        inf.inference()

        db.insert_cow_Video_Infomation_data(output_video=os.path.splitext(os.path.basename(output_path))[0])

        return jsonify(message='Inference completed', video_name=output_path)
    except Exception as e:
        return jsonify(message=f'Error: {str(e)}')



@app.route('/get_all_events', methods=['GET'])
def get_all_events():
    try:
        activity_filter = request.args.get('activity')   # e.g., 'Brushing'
        limit = request.args.get('limit', type=int)      # e.g., 100
        cow_id_filter = request.args.get('cow_id')       # optional filter by cow ID

        result = db.get_all_cow_events()
        df = pd.DataFrame(result, columns=['Cow-ID', 'Activity-Type', 'Duration', 'Video-Name', 'Date', 'Time', 'Camera'])

        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)

        # Apply filters
        if activity_filter:
            df = df[df['Activity-Type'].str.lower() == activity_filter.lower()]
        if cow_id_filter:
            df = df[df['Cow-ID'] == cow_id_filter]
        if limit:
            df = df.head(limit)

        # Format Video Name
        df['Video-Name'] = df['Video-Name'].apply(lambda x: f"{x.split('___')[1].strip()}.mp4" if '___' in x else x)

        df['Cow-ID'] = df['Cow-ID'].apply(lambda x: str(x).strip() if x and not isinstance(x, bytes) else 'New cow')

        # Format Date and Time
        df['Video-Date'] = df['Date'].apply(lambda x: datetime.strptime(x, "%Y%m%d").strftime("%Y-%m-%d") if isinstance(x, str) and len(x) == 8 else x)
        df['Video-Time'] = df['Time'].apply(lambda x: f"{x[:2]}:{x[2:4]}" if isinstance(x, str) and len(x) >= 4 else x)

        # Handle Headbutt Special Formatting
        headbutt_df = df[df['Activity-Type'] == 'Headbutt'].copy()
        headbutt_df = headbutt_df[headbutt_df['Cow-ID'].apply(lambda x: isinstance(x, str) and '-' in x)]
        split_cols = headbutt_df['Cow-ID'].str.split('-', expand=True)
        headbutt_df['Cow-ID 1'] = split_cols[0]
        headbutt_df['Cow-ID 2'] = split_cols[1]
        headbutt_df['Time of Occurrence'] = headbutt_df['Duration']
        headbutt_df.drop(columns=['Cow-ID', 'Duration'], inplace=True)

        normal_df = df[df['Activity-Type'] != 'Headbutt']
        combined_df = pd.concat([normal_df, headbutt_df], ignore_index=True)

        combined_df = combined_df.where(pd.notnull(combined_df), None)
        print("🔍 Any NaNs?", combined_df.isnull().sum())

        import numpy as np

        # Convert all NaNs to None
        combined_df = combined_df.replace({np.nan: None})

        return jsonify(combined_df.to_dict(orient='records'))
       

    except Exception as e:
        return jsonify(message=f'Error: {str(e)}'), 500


@app.route('/video_information', methods=['GET'])
def get_video_information():
    # Sample data or real query
    return jsonify({
        "message": "Video information endpoint working"
    })

@app.route('/get_all_videos', methods=['GET'])
def get_all_videos():
    try:
        result = db.get_video_info()
        videos = []

        for row in result:
            full_filename = row[0].split('/')[-1]  
            if 'Event' in full_filename:
                video_name = full_filename[full_filename.find('Event'):]
            else:
                video_name = full_filename

            # Ensure correct extension
            if not video_name.endswith('.mp4'):
                video_name += '.mp4'

            video_date = row[2].split(' ')[0]
            time_parts = row[2].split(' ')[1].split(':')
            video_time = f"{time_parts[0]}:{time_parts[1]}"

            annotated_path = os.path.join(annotated_folder, f"{os.path.splitext(video_name)[0]}.mp4")
            print(f"🔍 Checking for annotated video: {annotated_path} → {os.path.exists(annotated_path)}")


            videos.append({
                "Video-Name": video_name,
                "Preview-Video": f"input_video/{video_name}",
                "Inference-Status": "Processed" if os.path.exists(annotated_path) else "Not Processed",
                "video-Date": video_date,
                "video-Time": video_time
            })

        return jsonify(videos)
    except Exception as e:
        print(f"Error in /get_all_videos: {e}")
        return jsonify(message=f"Error: {str(e)}"), 500

import traceback  
@app.route('/static/Dataset/<path:filename>')
def serve_dataset_image(filename):
    return send_from_directory('static/Dataset', filename, mimetype='image/png')

@app.route('/get_cow_images', methods=['POST','GET'])
def get_cow_images():
    try:
        cluster_dict = training_image_clusters()
        response = db.get_cow_image_paths()
        df = pd.DataFrame(response, columns = ['Cow-ID', 'Video-Name', 'Date', 'Image-Paths','Cluster'])
        df["Image-Paths"] = df["Image-Paths"].apply(lambda x: x.split(';'))
        df = df.drop(columns=['Cow-ID','Video-Name','Date'])
        #print(cluster_dict)
        for id in cluster_dict:
            if id in df.Cluster.values:
                paths = list(df[df["Cluster"]==id]["Image-Paths"].values)[0]
                cluster_dict[id] = cluster_dict[id] + paths
        if "New" in list(df["Cluster"].values):
            cluster_dict["New"] = list(df[df["Cluster"]=="New"]["Image-Paths"].values)[0]
        #print(cluster_dict)
        df = pd.DataFrame(list(cluster_dict.items()), columns=['Cluster', 'Image-Paths'])
        df['Cluster'] = df['Cluster'].replace('New', 'cluster_999')
        df['Cluster'] = df['Cluster'].str.replace('cluster_', '').astype(int)
        df.sort_values(by='Cluster', inplace=True, ignore_index=True)
        df['Cluster'] = df['Cluster'].replace(999, 'New')
        df.reset_index(drop=True, inplace=True)
        json_data = df.to_dict(orient='records')
        
        return jsonify(json_data)
    
    except Exception as e:
        traceback.print_exc()  # ← This will print the full error in the terminal
        return jsonify(message=f'Error: {str(e)}'), 500

def training_image_clusters():
    path = r"Backend\static\Dataset"
    image_full_path = {}
    for folder in os.listdir(path):
        for image_path in os.listdir(os.path.join(path, folder)):
            if folder not in image_full_path:
                image_full_path[folder] = [os.path.join(path,folder,image_path)]
            else:
                image_full_path[folder].append(os.path.join(path,folder,image_path))
    return image_full_path


    
@app.route('/delete_events_for_video', methods=['DELETE'])
def delete_events_for_video():
    try:
        video_name = request.args.get('video_name')  

        if not video_name:
            return jsonify(message=" video_name is required"), 400

        db.delete_existing_events_for_video(video_name)
        return jsonify(message=f"Events for video {video_name} deleted successfully")

    except Exception as e:
        return jsonify(message=f"Error: {str(e)}"), 500

@app.route('/delete_all_events', methods=['DELETE'])
def delete_all_events():
    try:
        db.delete_all_events()
        return jsonify(message="✅ All CowEvents deleted successfully")
    except Exception as e:
        return jsonify(message=f"Error: {str(e)}"), 500


@app.route('/delete_all_videos', methods=['DELETE'])
def delete_all_videos():
    try:
        db.delete_all_videos()
        return jsonify(message="All videos deleted successfully")
    except Exception as e:
        return jsonify(message=f"Error: {str(e)}"), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)






