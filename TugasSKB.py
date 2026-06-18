import cv2
import threading
import geocoder as gcd
import random as rd
import time as tm
import psutil as pst
from flask import Flask, Response, render_template_string
from datetime import datetime as dt 

app = Flask(__name__)

# Inisialisasi Drone cam
cam = cv2.VideoCapture(0)

lock = threading.Lock()
output_frame = None

def update_droneCam():
    global cam, output_frame, lock
    
    interval_gps = 5000  
    time_prev_gps = 0
    lat = -6.2500
    long = 106.0000
    
    while True:
        st, fr = cam.read()
        if st:
            time_now = tm.monotonic() * 1000
            
            # Timestamp
            now = dt.now()
            cv2.putText(fr, f"Time: {now.strftime('%H:%M:%S')}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(fr, f"Date: {now.strftime('%Y/%m/%d')}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            # GPS
            if((time_now - time_prev_gps) >= interval_gps):
                lat = rd.uniform(-6.2500, -6.5500)    
                long = rd.uniform(106.0000, 106.3500) 
                time_prev_gps = time_now
            cv2.putText(fr, f"Loc: {lat:.4f}, {long:.4f}", (350, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            # Baterai
            bat_now = pst.sensors_battery()
            bat_pct = bat_now.percent if bat_now else 100 
            cv2.putText(fr, f"Batt: {bat_pct}%", (350, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                
            with lock:
                output_frame = fr.copy()

def frame_video():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None:
                continue
            rt, buf = cv2.imencode('.jpg', output_frame)
            
        byte_pix = buf.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + byte_pix + b'\r\n')

# 1. ROUTE HALAMAN LOGIN
@app.route('/')
def index():
    html_login = """
    <html lang="id">
    <head>
    <meta charset="UTF-8">
    <title>Login Simple</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; }
        h2 { text-align: center; margin-bottom: 20px; color: #333; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; margin-bottom: 5px; color: #666; }
        .input-group input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #007bff; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #0056b3; }
        .message { margin-top: 15px; text-align: center; font-weight: bold; }
    </style>
    </head>
    <body>
    <div class="login-container">
        <h2>Form Login Monitor</h2>
        <form id="loginForm">
            <div class="input-group">
                <label for="username">Username:</label>
                <input type="text" id="username" required>
            </div>
            <div class="input-group">
                <label for="password">Password:</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit">Masuk</button>
        </form>
        <div id="message" class="message"></div>
    </div>

    <script>
    const USERNAME_BENAR = "admin";
    const PASSWORD_BENAR = "kelompok_3";

    document.getElementById('loginForm').addEventListener('submit', function(event) {
        event.preventDefault(); 
        const usernameInput = document.getElementById('username').value;
        const passwordInput = document.getElementById('password').value;
        const messageDiv = document.getElementById('message');

        if (usernameInput === USERNAME_BENAR && passwordInput === PASSWORD_BENAR) {
            messageDiv.style.color = "green";
            messageDiv.textContent = "Login Berhasil! Mengalihkan...";
            
            setTimeout(function() {
                window.location.href = "/dashboard"; 
            }, 1000);
        } else {
            messageDiv.style.color = "red";
            messageDiv.textContent = "Usnm atau Psd salah!";
        }
    });
    </script>
    </body>
    </html>
    """
    return render_template_string(html_login)

# 2. ROUTE HALAMAN DASHBOARD (SIMULASI KOORDINAT)
@app.route('/dashboard')
def dashboard():
    html_dashboard = """
    <html lang="id">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Deteksi Koordinat</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100vh;
        margin: 0;
        background-color: #f4f4f9;
      }

      h3 { margin-bottom: 5px; }
      p { margin-top: 0; color: #666; }

      .coordinate-plane {
        position: relative;
        width: 800px;  
        height: 500px; 
        border: 3px solid #333;
        background-color: #ffffff;
        background-image: 
          linear-gradient(to right, #eee 1px, transparent 1px),
          linear-gradient(to bottom, #eee 1px, transparent 1px);
        background-size: 50px 50px;
      }

      .square {
        position: absolute;
        width: 50px;
        height: 50px;
        background-color: #3498db;
        border-radius: 4px;
        transition: all 0.2s ease;
        left: 0px;
        top: 0px;
        z-index: 2;
      }

      .square.detected {
        background-color: #f1c40f; 
        transform: scale(1.1);    
        box-shadow: 0 0 15px #f1c40f;
      }

      .target-point {
        position: absolute;
        width: 50px;
        height: 50px;
        background-color: #e74c3c; 
        border-radius: 50%;        
        opacity: 0.7;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 11px;
        font-weight: bold;
      }

      .status-panel {
        margin-top: 15px;
        font-size: 16px;
        text-align: center;
      }

      .alert-box {
        margin-top: 10px;
        padding: 10px 20px;
        font-weight: bold;
        border-radius: 5px;
        background-color: #bdc3c7;
        color: #333;
        transition: all 0.2s ease;
      }

      .alert-box.active {
        background-color: #2ecc71; 
        color: white;
        animation: pulse 0.5s infinite alternate;
      }

      @keyframes pulse {
        from { transform: scale(1); }
        to { transform: scale(1.03); }
      }

      .nav-btn {
        margin-top: 20px;
        padding: 10px 25px;
        background-color: #34495e;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-weight: bold;
        transition: background-color 0.2s;
      }
      .nav-btn:hover {
        background-color: #2c3e50;
      }
      </style>
      </head>
      <body>

      <h3>Deteksi TPS Liar</h3>
      <p>Drone (warna biru) akan mendeteksi TPS Liar (titik merah) saat melewatinya</p>

      <div class="coordinate-plane">
        <div class="target-point" id="target" style="left: 150px; top: 100px;">TPS</div>
        <div class="square" id="movingSquare"></div>
      </div>

      <div class="status-panel">
        <div>Posisi Drone: <b>X = <span id="posX">0</span>px, Y = <span id="posY">0</span>px</b></div>
        <div class="alert-box" id="detectorAlert">Sistem: MENCARI TPS LIAR...</div>
      </div>

      <a href="/live_feed" class="nav-btn">Live Feed</a>

      <script>
      let stt = 0;
      let currentX = 0;
      let currentY = 0;
      const square = document.getElementById('movingSquare');
      const target = document.getElementById('target');
      const posXDisplay = document.getElementById('posX');
      const posYDisplay = document.getElementById('posY');
      const detectorAlert = document.getElementById('detectorAlert');
      const step = 50;        
      const maxWidth = 800;   
      const maxHeight = 500;  
      const targetX = parseInt(target.style.left);
      const targetY = parseInt(target.style.top);

      function jalankanSistem() {
        if (stt === 0) {
          currentX += step;
          if (currentX >= maxWidth) {
            currentX = maxWidth - 50;        
            currentY += step;  
            stt = 1;  
          }
        }
        else {
          currentX -= step;
          if (currentX <= -50) {
            currentX = 0;        
            currentY += step;  
            stt = 0;
          }
        }
        if (currentY >= maxHeight) {
          currentX = 0;        
          currentY = 0;
        }

        square.style.left = currentX + 'px';
        square.style.top = currentY + 'px';

        posXDisplay.textContent = currentX;
        posYDisplay.textContent = currentY;

        if (currentX === targetX && currentY === targetY) {
          square.classList.add('detected');
          detectorAlert.classList.add('active');
          detectorAlert.textContent = " TPS LIAR TERDETEKSI DI (" + targetX + "px, " + targetY + "px)!";
        } 
        else {
          square.classList.remove('detected');
          detectorAlert.classList.remove('active');
          detectorAlert.textContent = "DRONE: MENCARI TPS LIAR...";
        }
      }
      setInterval(jalankanSistem, 500);
      </script>

      </body>
    </html>
    """
    return render_template_string(html_dashboard)

# 3. ROUTE HALAMAN MONITOR LIVE FEED HTML
@app.route('/live_feed')
def live_feed():
    html_live = """
    <html>
        <head>
            <title>Dashboard Live Feed Drone</title>
            <style>
            .back-btn {
              margin-top: 20px;
              display: inline-block;
              padding: 10px 20px;
              background-color: #7f8c8d;
              color: white;
              text-decoration: none;
              border-radius: 4px;
              font-weight: bold;
            }
            .back-btn:hover {
              background-color: #2c3e50;
            }
            </style>
        </head>
        <body style="text-align: center; font-family: Arial, sans-serif; background-color: #222; color: yellow;">
            <h1>Simulasi Data Video Feed Stream Monitor dari Drone</h1>
            <div style="margin-top: 20px;">
                <img src="/video_feed" width="700" style="border: 5px solid #00ff00; border-radius: 10px;">
            </div>
            <br><br>
            <a href="/dashboard" class="back-btn">Kembali ke Simulasi</a>
        </body>
    </html>
    """
    return render_template_string(html_live)

# 4. ROUTE BINARY STREAM VIDEO MJPEG (Arah sumber tag <img>)
@app.route('/video_feed')
def video_feed():
    return Response(frame_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    thr = threading.Thread(target=update_droneCam)
    thr.daemon = True
    thr.start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
