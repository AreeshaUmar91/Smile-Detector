import cv2
import numpy as np
import math
import os
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from PIL import Image, ImageTk
import datetime
import threading
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re  # For email validation

# Load pre-trained models
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
    
    # Verify cascades loaded properly
    if face_cascade.empty():
        print("Error: Failed to load face cascade classifier")
    if smile_cascade.empty():
        print("Error: Failed to load smile cascade classifier")
except Exception as e:
    print(f"Error loading cascade files: {e}")

# Create directory for saved images if it doesn't exist
SAVE_DIRECTORY = "captured_images"
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

class FaceDetectionApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1200x700")
        
        # Set theme colors
        self.primary_color = "#4a6cd4"  # Blue as primary color
        self.accent_color = "#f25d50"   # Coral as accent
        self.bg_color = "#f5f5f7"       # Light gray background
        self.text_color = "#333333"     # Dark text
        self.light_color = "#ffffff"    # White
        
        # Configure window style
        self.window.configure(bg=self.bg_color)
        
        # Pre-configured email settings
        self.email_recipient = "developer1@gmail.com"
        self.email_sender = "developer1@gmail.com"
        self.email_password = "dwkr lahn knxn yjve"
        self.email_server = "smtp.gmail.com"
        self.email_port = 587
        self.auto_email = True  # Auto-email is enabled by default
        
        # Auto-capture mode (default to Auto)
        self.auto_capture_mode = True
        
        # Check if camera is available
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.show_camera_error()
            return
            
        self.is_capturing = True
        
        # Configure modern styles
        self.configure_styles()
        
        # Create UI elements
        self.create_ui()
        
        # Start video thread
        self.video_thread = threading.Thread(target=self.update, daemon=True)
        self.video_thread.start()
        
        # Store captured images
        self.captured_images = []
        self.load_existing_images()
        
        # Update the window
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def configure_styles(self):
        """Configure custom styles for the app"""
        style = ttk.Style()
        
        # Configure main styles
        style.configure("TFrame", background=self.bg_color)
        style.configure("Light.TFrame", background=self.light_color)
        
        # Labelframe styles
        style.configure("TLabelframe", background=self.light_color, borderwidth=1)
        style.configure("TLabelframe.Label", foreground=self.text_color, background=self.light_color, 
                        font=("Segoe UI", 11, "bold"))
        
        # Button styles
        style.configure("TButton", font=("Segoe UI", 10), background=self.primary_color, 
                     foreground="black", borderwidth=0)
        style.map("TButton", 
                background=[("active", self.primary_color), ("pressed", "#3a5cc4")],
                foreground=[("active", self.light_color), ("pressed", self.light_color)])
        
        # Accent button style
        style.configure("Accent.TButton", background=self.accent_color,foreground="black")
        style.map("Accent.TButton", 
                background=[("active", self.accent_color), ("pressed", "#e24d40")])
        
        # Label styles
        style.configure("TLabel", background=self.light_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=self.bg_color, foreground=self.primary_color, font=("Segoe UI", 9, "italic"))
        style.configure("Gallery.TLabel", background=self.light_color, foreground="#555555", font=("Segoe UI", 9))
        
        # Gallery item style
        style.configure("Gallery.TFrame", background=self.light_color, borderwidth=1, relief="solid")
    
    def show_camera_error(self):
        """Show error message when camera is not available"""
        error_frame = ttk.Frame(self.window, padding=20, style="TFrame")
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add an error icon
        error_icon = "❌"  # Unicode error symbol
        error_icon_label = ttk.Label(
            error_frame, 
            text=error_icon,
            font=("Segoe UI", 48),
            foreground="red"
        )
        error_icon_label.pack(pady=(30, 10))
        
        error_label = ttk.Label(
            error_frame, 
            text="Camera not available!",
            font=("Segoe UI", 16, "bold"),
            foreground="red"
        )
        error_label.pack(pady=(0, 10))
        
        error_detail = ttk.Label(
            error_frame, 
            text="Please check if your webcam is connected and not in use by another application.",
            font=("Segoe UI", 12)
        )
        error_detail.pack(pady=(0, 30))
        
        retry_button = ttk.Button(
            error_frame,
            text="🔄 Retry Connection",
            command=self.retry_camera_connection,
            style="Accent.TButton"
        )
        retry_button.pack(pady=20, ipadx=10, ipady=5)
    
    def retry_camera_connection(self):
        """Try to reconnect to the camera"""
        if self.cap.isOpened():
            self.cap.release()
            
        self.cap = cv2.VideoCapture(0)
        
        if self.cap.isOpened():
            # Clear the window
            for widget in self.window.winfo_children():
                widget.destroy()
                
            # Restart the app components
            self.is_capturing = True
            self.create_ui()
            self.video_thread = threading.Thread(target=self.update, daemon=True)
            self.video_thread.start()
            self.captured_images = []
            self.load_existing_images()
        else:
            # Update error message
            error_label = ttk.Label(
                self.window, 
                text="Still unable to connect to camera.\nPlease verify your webcam is properly connected.",
                font=("Segoe UI", 14),
                foreground="red"
            )
            error_label.pack(pady=30)
    
    def create_ui(self):
        # Create app header
        header_frame = ttk.Frame(self.window, style="TFrame")
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # App title with emoji
        app_title = ttk.Label(
            header_frame, 
            text="😄 Smile Detection App", 
            font=("Segoe UI", 18, "bold"), 
            foreground=self.primary_color,
            style="TLabel"
        )
        app_title.pack(side=tk.LEFT, padx=5)
        
        # App subtitle
        app_subtitle = ttk.Label(
            header_frame, 
            text="Capture your best smiles automatically", 
            font=("Segoe UI", 10, "italic"),
            foreground="#666666",
            style="TLabel"
        )
        app_subtitle.pack(side=tk.LEFT, padx=15, pady=5)
        
        # Create main frame with two columns
        main_frame = ttk.Frame(self.window, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Left column for webcam with rounded corners
        self.left_frame = ttk.LabelFrame(main_frame, text=" 📹 Live Camera ")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Video display with shadow effect
        video_frame = ttk.Frame(self.left_frame, style="Light.TFrame")
        video_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        # Add placeholder image with gradient background
        placeholder = np.ones((480, 640, 3), dtype=np.uint8) * 220
        
        # Create a gradient background
        for y in range(placeholder.shape[0]):
            for x in range(placeholder.shape[1]):
                ratio_y = y / placeholder.shape[0]
                color = (int(220 * (1-ratio_y) + 180 * ratio_y),
                         int(220 * (1-ratio_y) + 200 * ratio_y),
                         int(220 * (1-ratio_y) + 240 * ratio_y))
                placeholder[y, x] = color
        
        # Add text and camera icon to placeholder
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Starting camera..."
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        text_x = (placeholder.shape[1] - textsize[0]) // 2
        text_y = (placeholder.shape[0] + textsize[1]) // 2
        
        # Add camera icon
        icon_text = "📷"
        icon_size = cv2.getTextSize(icon_text, font, 2, 2)[0]
        icon_x = (placeholder.shape[1] - icon_size[0]) // 2
        icon_y = text_y - 50
        
        cv2.putText(placeholder, icon_text, (icon_x, icon_y), font, 2, (80, 80, 120), 2, cv2.LINE_AA)
        cv2.putText(placeholder, text, (text_x, text_y), font, 1, (50, 50, 70), 2, cv2.LINE_AA)
        
        # Convert to PhotoImage
        placeholder_img = cv2.cvtColor(placeholder, cv2.COLOR_BGR2RGB)
        placeholder_img = Image.fromarray(placeholder_img)
        self.placeholder_photo = ImageTk.PhotoImage(image=placeholder_img)
        
        # Create a frame to hold the video with a border
        video_container = ttk.Frame(video_frame, style="Light.TFrame")
        video_container.pack(padx=8, pady=8)
        
        # Video display label
        self.video_label = ttk.Label(video_container, image=self.placeholder_photo, borderwidth=2, relief="solid")
        self.video_label.pack()
        
        # Mode display frame
        mode_frame = ttk.Frame(self.left_frame, style="Light.TFrame")
        mode_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Status indicator - create a color indicator
        status_indicator = tk.Canvas(mode_frame, width=15, height=15, bg=self.bg_color, highlightthickness=0)
        status_indicator.create_oval(2, 2, 13, 13, fill="green", outline="")
        status_indicator.pack(side=tk.LEFT, padx=5)
        
        # Status text with better styling
        self.status_label = ttk.Label(
            mode_frame, 
            text="Auto-capture mode is active",
            font=("Segoe UI", 10, "italic"),
            foreground="#008800",
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Control panel with gradient background
        control_panel = ttk.Frame(self.left_frame, style="Light.TFrame")
        control_panel.pack(fill=tk.X, padx=15, pady=10)
        
        # Button with modern styling
        button_frame = ttk.Frame(control_panel, style="Light.TFrame")
        button_frame.pack(pady=10)
        
        # Capture button with accent style
        self.capture_btn = ttk.Button(
            button_frame, 
            text="📸 Manual Capture", 
            command=lambda: self.capture_image(),
            style="Accent.TButton"
        )
        self.capture_btn.pack(side=tk.LEFT, padx=10, ipadx=10, ipady=5)
        
        # Toggle mode button with primary style
        self.mode_btn = ttk.Button(
            button_frame, 
            text="🔄 Mode: Auto", 
            command=self.toggle_capture_mode
        )
        self.mode_btn.pack(side=tk.LEFT, padx=10, ipadx=10, ipady=5)
        
        # Email status with icon
        email_frame = ttk.Frame(control_panel, style="Light.TFrame")
        email_frame.pack(fill=tk.X, pady=10)
        
        email_icon_label = ttk.Label(
            email_frame, 
            text="📧", 
            font=("Segoe UI", 12),
            style="TLabel"
        )
        email_icon_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.email_status = ttk.Label(
            email_frame, 
            text=f"Email: {self.email_recipient}", 
            font=("Segoe UI", 10),
            style="TLabel"
        )
        self.email_status.pack(side=tk.LEFT)
        
        # Auto-send status with toggle indicator
        auto_send_frame = ttk.Frame(email_frame, style="Light.TFrame")
        auto_send_frame.pack(side=tk.RIGHT, padx=10)
        
        auto_send_label = ttk.Label(
            auto_send_frame, 
            text="Auto-send:", 
            font=("Segoe UI", 10),
            style="TLabel"
        )
        auto_send_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create a toggle indicator (green for ON)
        toggle_indicator = tk.Canvas(auto_send_frame, width=30, height=16, bg=self.light_color, highlightthickness=0)
        toggle_indicator.create_rectangle(0, 0, 30, 16, fill="#4CAF50", outline="")
        toggle_indicator.create_oval(14, 0, 30, 16, fill="white", outline="")
        toggle_indicator.pack(side=tk.LEFT)
        
        # Right column for gallery with modern styling
        self.right_frame = ttk.LabelFrame(main_frame, text=" 📷 Smile Gallery ")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create a canvas with a scrollbar for the gallery
        self.canvas_frame = ttk.Frame(self.right_frame, style="Light.TFrame")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Gallery header with count
        gallery_header = ttk.Frame(self.canvas_frame, style="Light.TFrame")
        gallery_header.pack(fill=tk.X, pady=(0, 10))
        
        self.gallery_count = ttk.Label(
            gallery_header,
            text="Captured images: 0",
            font=("Segoe UI", 10),
            style="Gallery.TLabel"
        )
        self.gallery_count.pack(side=tk.LEFT)
        
        # Create a styled canvas for the gallery
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.light_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Light.TFrame")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # App footer with version and author info
        footer_frame = ttk.Frame(self.window, style="TFrame")
        footer_frame.pack(fill=tk.X, padx=15, pady=5)
        
        footer_text = ttk.Label(
            footer_frame,
            text="Smile Detection App v2.0 - Your smiles, captured perfectly",
            font=("Segoe UI", 8),
            foreground="#888888",
            style="TLabel"
        )
        footer_text.pack(side=tk.RIGHT)
    
    def toggle_capture_mode(self):
        """Toggle between auto-capture and manual capture modes with modern notification"""
        self.auto_capture_mode = not self.auto_capture_mode
        
        if self.auto_capture_mode:
            # Set to auto mode
            self.mode_btn.config(text="🔄 Mode: Auto")
            self.status_label.config(text="Auto-capture mode is active", foreground="#008800")
        else:
            # Set to manual mode
            self.mode_btn.config(text="🔄 Mode: Manual")
            self.status_label.config(text="Manual capture mode - Click to capture", foreground="#d94c4c")
        
        # Create a sleek notification
        self.show_notification(
            title="Mode Changed",
            message=f"Capture mode changed to: {'Auto' if self.auto_capture_mode else 'Manual'}",
            duration=1500
        )
    
    def show_notification(self, title, message, duration=2000):
        """Show a modern floating notification"""
        notification = tk.Toplevel(self.window)
        notification.title("")
        notification.geometry("320x100")
        notification.overrideredirect(True)  # Remove window border
        notification.attributes('-topmost', True)
        notification.configure(bg=self.light_color)
        
        # Calculate position (bottom right corner)
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        # Position notification at the bottom right
        x_pos = window_x + window_width - 340
        y_pos = window_y + window_height - 120
        notification.geometry(f"+{x_pos}+{y_pos}")
        
        # Create a frame with a border
        frame = tk.Frame(notification, bg=self.light_color, bd=1, relief="solid")
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Header with title and close button
        header = tk.Frame(frame, bg=self.primary_color)
        header.pack(fill="x")
        
        title_label = tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), bg=self.primary_color, fg="white")
        title_label.pack(side="left", padx=10, pady=3)
        
        close_button = tk.Label(header, text="×", font=("Segoe UI", 12), bg=self.primary_color, fg="white", cursor="hand2")
        close_button.pack(side="right", padx=10, pady=3)
        close_button.bind("<Button-1>", lambda e: notification.destroy())
        
        # Message content
        content = tk.Frame(frame, bg=self.light_color)
        content.pack(fill="both", expand=True)
        
        message_label = tk.Label(content, text=message, font=("Segoe UI", 10), bg=self.light_color)
        message_label.pack(padx=15, pady=15)
        
        # Auto-close after duration
        notification.after(duration, notification.destroy)
    
    def send_email_with_image(self, image_path):
        """Send an email with the captured image as an attachment with improved spam prevention"""
        if not self.email_recipient or not self.email_sender or not self.email_password:
            return False
        
        try:
            # Set up the SMTP server
            server = smtplib.SMTP(self.email_server, self.email_port)
            server.starttls()
            server.login(self.email_sender, self.email_password)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"Smile Detection App <{self.email_sender}>"
            msg['To'] = self.email_recipient
            msg['Subject'] = "Smile Detected - New Captured Image"
            
            # Message body - more professional content to avoid spam filters
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # HTML Body with better formatting (helps avoid spam filters)
            html_body = f"""
            <html>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f7;">
                <div style="background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #4a6cd4; margin-top: 0;">New Smile Detected! 😄</h2>
                    <p>Hello,</p>
                    <p>Your Smile Detection App has captured a new smile at <b>{current_time}</b>.</p>
                    <p>The captured image is attached to this email.</p>
                    <div style="margin: 20px 0; padding: 15px; background-color: #f0f4ff; border-left: 4px solid #4a6cd4; border-radius: 4px;">
                        <p style="margin: 0; color: #555;">Smile Detection App is automatically capturing your best moments!</p>
                    </div>
                    <p>Best regards,<br>
                    Your Smile Detection App</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text alternative
            text_body = f"""
            New Smile Detected!
            
            Hello,
            
            Your Smile Detection App has captured a new smile at {current_time}.
            The captured image is attached to this email.
            
            Best regards,
            Your Smile Detection App
            """
            
            # Add plain text part
            msg.attach(MIMEText(text_body, 'plain'))
            
            # Add HTML part
            msg.attach(MIMEText(html_body, 'html'))
            
            # Add custom headers to prevent spam classification
            msg.add_header('X-Priority', '1')  # High priority
            msg.add_header('X-MSMail-Priority', 'High')
            msg.add_header('X-Mailer', 'Microsoft Outlook')
            msg.add_header('Importance', 'High')
            
            # Attach image
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                image = MIMEImage(img_data, name=os.path.basename(image_path))
                image.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(image_path)}"')
                msg.attach(image)
            
            # Send the email
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def update(self):
        # Variables to track face detection and capture timing
        last_capture_time = 0
        capture_delay = 2  # Delay between captures in seconds
        error_count = 0
        max_errors = 5
        
        while self.is_capturing:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    error_count += 1
                    if error_count > max_errors:
                        print("Too many frame errors. Camera may be disconnected.")
                        break
                    time.sleep(0.1)
                    continue
                
                # Reset error count on successful frame
                error_count = 0
                
                # Apply facial attribute detection and check if faces were detected
                result, face_detected, is_smiling = self.detect_facial_attributes(frame)
                
                # Auto-capture logic - capture any face detected
                current_time = time.time()
                if self.auto_capture_mode and face_detected and current_time - last_capture_time > capture_delay:
                    # Capture image whenever a face is detected
                    self.capture_image(result)
                    last_capture_time = current_time
                
                # Convert to RGB for tkinter
                cv_image = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                
                # Convert to PhotoImage
                img = Image.fromarray(cv_image)
                img = img.resize((640, 480), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(image=img)
                
                # Update video label
                self.video_label.config(image=self.photo)
                self.video_label.image = self.photo
                
            except Exception as e:
                print(f"Error in video processing: {e}")
                time.sleep(0.1)
        
    def detect_facial_attributes(self, frame):
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Flag to track if faces are detected
        face_detected = False
        is_smiling = False
        
        # Detect faces - improved parameters for better distance detection
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,  # Reduced for better detection
            minSize=(20, 20)  # Smaller minimum size to detect faces from a distance
        )
        
        # For each face, detect smiles only
        for (x, y, w, h) in faces:
            # Mark that we've detected a face
            face_detected = True
            
            # Extract face region
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            # Draw face rectangle with modern design (rounded corners effect)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (74, 108, 212), 3, cv2.LINE_AA)
            
            # Draw corner markers for a more modern look
            corner_length = 20  # Length of corner marker
            thickness = 3       # Thickness of corner marker
            color = (74, 108, 212)  # Primary color
            
            # Top-left corner
            cv2.line(frame, (x, y), (x + corner_length, y), color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x, y), (x, y + corner_length), color, thickness, cv2.LINE_AA)
            
            # Top-right corner
            cv2.line(frame, (x + w, y), (x + w - corner_length, y), color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x + w, y), (x + w, y + corner_length), color, thickness, cv2.LINE_AA)
            
            # Bottom-left corner
            cv2.line(frame, (x, y + h), (x + corner_length, y + h), color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x, y + h), (x, y + h - corner_length), color, thickness, cv2.LINE_AA)
            
            # Bottom-right corner
            cv2.line(frame, (x + w, y + h), (x + w - corner_length, y + h), color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_length), color, thickness, cv2.LINE_AA)
            
            # Detect smiles within the face
            smiles = smile_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.3,
                minNeighbors=10,
                minSize=(15, 15)
            )
            
            # Determine smile status
            if len(smiles) > 0:
                is_smiling = True
                smile_message = "SMILE DETECTED"
                smile_color = (0, 255, 0)  # Green color
                
                # Draw smile rectangles
                for (sx, sy, sw, sh) in smiles:
                    cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), (0, 255, 0), 2, cv2.LINE_AA)
            else:
                smile_message = "NO SMILE"
                smile_color = (0, 0, 255)  # Red color
            
            # Create a more modern label with rounded rectangle background
            text_size = cv2.getTextSize(smile_message, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = x + (w - text_size[0]) // 2  # Center horizontally
            text_y = y - 15  # Position above the face
            
            # If would be off-screen, move below face
            if text_y < 15:
                text_y = y + h + 30  # Position below the face
                
            # Draw modern pill-shaped background for status text
            pill_padding = 10
            bg_x1 = text_x - pill_padding
            bg_x2 = text_x + text_size[0] + pill_padding
            bg_y1 = text_y - text_size[1] - pill_padding // 2
            bg_y2 = text_y + pill_padding // 2
            
            # Draw background with rounded corners effect
            overlay = frame.copy()
            # Filled rectangle
            cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), 
                         (30, 30, 30), -1, cv2.LINE_AA)
                         
            # Apply overlay with transparency
            alpha = 0.7
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            # Draw the smile text
            cv2.putText(frame, smile_message, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, smile_color, 2, cv2.LINE_AA)
        
        return frame, face_detected, is_smiling
    
    def capture_image(self, frame=None):
        """Capture the current frame and save it with enhanced styling"""
        if frame is None:
            # Get current frame if not provided
            ret, frame = self.cap.read()
            if not ret:
                return
            # Apply detection before saving
            result, _, _ = self.detect_facial_attributes(frame)
        else:
            result = frame
            
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SAVE_DIRECTORY}/face_{timestamp}.jpg"
        
        # Save image
        cv2.imwrite(filename, result)
        
        # Add to gallery
        self.add_image_to_gallery(filename)
        
        # Update gallery count
        if hasattr(self, 'gallery_count'):
            self.gallery_count.config(text=f"Captured images: {len(self.captured_images)}")
        
        # Send email when auto_email is on
        email_sent = False
        if self.auto_email:
            email_sent = self.send_email_with_image(filename)
        
        # Show sleek notification with custom styling
        if self.auto_capture_mode:
            if email_sent:
                title = "Auto-Capture Success"
                message = "Image auto-captured and sent by email"
            else:
                title = "Auto-Capture Success"
                message = "Image automatically captured and saved"
        else:
            if email_sent:
                title = "Manual Capture"
                message = "Image captured and sent by email"
            else:
                title = "Manual Capture"
                message = "Image captured and saved successfully"
                
        self.show_notification(title, message)
    
    def add_image_to_gallery(self, image_path):
        """Add an image to the gallery with enhanced modern styling"""
        try:
            # Create a frame for this image with shadow effect
            img_frame = ttk.Frame(self.scrollable_frame, style="Gallery.TFrame")
            img_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Load and resize image
            img = Image.open(image_path)
            img = img.resize((200, 160), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Get image timestamp and format it nicely
            timestamp_parts = os.path.basename(image_path).split('_')[1].split('.')[0]
            year = timestamp_parts[:4]
            month = timestamp_parts[4:6]
            day = timestamp_parts[6:8]
            hour = timestamp_parts[8:10]
            minute = timestamp_parts[10:12]
            second = timestamp_parts[12:14]
            formatted_time = f"{day}/{month}/{year} at {hour}:{minute}:{second}"
            
            # Create an elegant container with white background
            content_frame = ttk.Frame(img_frame, style="Light.TFrame")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Image container with border
            img_container = ttk.Frame(content_frame, style="Light.TFrame")
            img_container.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Add image with shadow effect (using nested frames)
            img_outer = ttk.Frame(img_container, style="Light.TFrame")
            img_outer.pack(padx=2, pady=2)
            
            # Image label
            img_label = ttk.Label(img_outer, image=photo, borderwidth=1, relief="solid")
            img_label.image = photo  # Keep a reference
            img_label.pack()
            
            # Create info panel with elegant styling
            info_frame = ttk.Frame(content_frame, style="Light.TFrame")
            info_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y, expand=True)
            
            # Details section
            details_frame = ttk.Frame(info_frame, style="Light.TFrame")
            details_frame.pack(fill=tk.X, pady=(10, 5), anchor="w")
            
            # Calendar icon and capture time
            time_frame = ttk.Frame(details_frame, style="Light.TFrame")
            time_frame.pack(fill=tk.X, pady=2, anchor="w")
            
            calendar_label = ttk.Label(time_frame, text="🗓️", font=("Segoe UI", 11), style="TLabel")
            calendar_label.pack(side=tk.LEFT)
            
            time_label = ttk.Label(time_frame, text=f"Captured: {formatted_time}", 
                                  font=("Segoe UI", 9), style="Gallery.TLabel")
            time_label.pack(side=tk.LEFT, padx=5)
            
            # File info
            file_frame = ttk.Frame(details_frame, style="Light.TFrame")
            file_frame.pack(fill=tk.X, pady=2, anchor="w")
            
            file_icon = ttk.Label(file_frame, text="📄", font=("Segoe UI", 11), style="TLabel")
            file_icon.pack(side=tk.LEFT)
            
            file_label = ttk.Label(file_frame, text=os.path.basename(image_path), 
                                  font=("Segoe UI", 9), style="Gallery.TLabel")
            file_label.pack(side=tk.LEFT, padx=5)
            
            # Actions section with modern buttons
            actions_frame = ttk.Frame(info_frame, style="Light.TFrame")
            actions_frame.pack(fill=tk.X, pady=10)
            
            # Email button with icon
            email_btn = ttk.Button(actions_frame, text="📧 Email", width=10,
                                command=lambda path=image_path: self.send_email_with_image(path))
            email_btn.pack(side=tk.LEFT, padx=5)
            
            # Delete button with icon and accent style
            delete_btn = ttk.Button(actions_frame, text="🗑️ Delete", width=10, style="Accent.TButton",
                                   command=lambda path=image_path, frame=img_frame: self.delete_image(path, frame))
            delete_btn.pack(side=tk.LEFT, padx=5)
            
            # Store image info
            self.captured_images.append({"path": image_path, "frame": img_frame})
            
            # Update scrollbar
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Update gallery count
            if hasattr(self, 'gallery_count'):
                self.gallery_count.config(text=f"Captured images: {len(self.captured_images)}")
                
        except Exception as e:
            print(f"Error adding image to gallery: {e}")
    
    def delete_image(self, image_path, frame):
        """Delete an image from disk and gallery with confirmation"""
        # Create confirmation dialog
        confirm = tk.Toplevel(self.window)
        confirm.title("Confirm Delete")
        confirm.geometry("350x150")
        confirm.configure(bg=self.light_color)
        confirm.resizable(False, False)
        confirm.transient(self.window)
        confirm.grab_set()
        
        # Center the dialog
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        x_pos = window_x + (window_width - 350) // 2
        y_pos = window_y + (window_height - 150) // 2
        confirm.geometry(f"+{x_pos}+{y_pos}")
        
        # Dialog content
        frame_inner = ttk.Frame(confirm, style="Light.TFrame")
        frame_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Warning icon
        warning_label = ttk.Label(frame_inner, text="⚠️", font=("Segoe UI", 24), style="TLabel")
        warning_label.pack(pady=(15, 5))
        
        # Warning message
        message_label = ttk.Label(
            frame_inner, 
            text="Are you sure you want to delete this image?", 
            font=("Segoe UI", 11),
            style="TLabel"
        )
        message_label.pack(pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(frame_inner, style="Light.TFrame")
        button_frame.pack(pady=10)
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=confirm.destroy,
            width=8
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Delete button with accent style
        def confirm_delete():
            # Remove from disk
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # Remove from UI
            frame.destroy()
            
            # Remove from list
            self.captured_images = [img for img in self.captured_images if img["path"] != image_path]
            
            # Update scrollbar
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Update gallery count
            if hasattr(self, 'gallery_count'):
                self.gallery_count.config(text=f"Captured images: {len(self.captured_images)}")
            
            # Show notification
            self.show_notification("Image Deleted", "Image has been successfully deleted")
            
            # Close dialog
            confirm.destroy()
        
        delete_btn = ttk.Button(
            button_frame, 
            text="Delete", 
            command=confirm_delete,
            style="Accent.TButton",
            width=8
        )
        delete_btn.pack(side=tk.LEFT, padx=10)
    
    def load_existing_images(self):
        """Load existing images from the save directory with progress indicator"""
        if not os.path.exists(SAVE_DIRECTORY):
            return
            
        files = [f for f in os.listdir(SAVE_DIRECTORY) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        if not files:
            return
            
        # Show loading indicator for larger galleries
        if len(files) > 5:
            loading_label = ttk.Label(
                self.scrollable_frame,
                text="Loading images...",
                font=("Segoe UI", 10, "italic"),
                style="Gallery.TLabel"
            )
            loading_label.pack(pady=20)
            self.canvas.update_idletasks()
        
        # Load images
        for filename in files:
            image_path = os.path.join(SAVE_DIRECTORY, filename)
            self.add_image_to_gallery(image_path)
            
        # Remove loading indicator if it exists
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text") == "Loading images...":
                widget.destroy()
                break
    
    def on_closing(self):
        """Clean up resources when closing with confirmation"""
        # Create confirmation dialog for exit
        confirm = tk.Toplevel(self.window)
        confirm.title("Exit Application")
        confirm.geometry("350x150")
        confirm.configure(bg=self.light_color)
        confirm.resizable(False, False)
        confirm.transient(self.window)
        confirm.grab_set()
        
        # Center dialog
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        x_pos = window_x + (window_width - 350) // 2
        y_pos = window_y + (window_height - 150) // 2
        confirm.geometry(f"+{x_pos}+{y_pos}")
        
        # Dialog content
        frame_inner = ttk.Frame(confirm, style="Light.TFrame")
        frame_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Question icon
        icon_label = ttk.Label(frame_inner, text="❓", font=("Segoe UI", 24), style="TLabel")
        icon_label.pack(pady=(15, 5))
        
        # Message
        message_label = ttk.Label(
            frame_inner, 
            text="Are you sure you want to exit the application?", 
            font=("Segoe UI", 11),
            style="TLabel"
        )
        message_label.pack(pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(frame_inner, style="Light.TFrame")
        button_frame.pack(pady=10)
        
        # Function to actually close app
        def do_close():
            self.is_capturing = False
            if hasattr(self, 'video_thread') and self.video_thread.is_alive():
                self.video_thread.join(1.0)
            if self.cap.isOpened():
                self.cap.release()
            self.window.destroy()
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=confirm.destroy,
            width=8
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Exit button
        exit_btn = ttk.Button(
            button_frame, 
            text="Exit", 
            command=do_close,
            style="Accent.TButton",
            width=8
        )
        exit_btn.pack(side=tk.LEFT, padx=10)

def main():
    # Create tkinter window with app icon
    root = tk.Tk()
    root.title("Smile Detection App")
    
    # Set a nice window icon if available
    try:
        # Try to create a simple smile emoji as icon using a PhotoImage
        icon = tk.PhotoImage(width=64, height=64)
        for y in range(64):
            for x in range(64):
                # Create a yellow circle
                dx, dy = x-32, y-32
                inside_circle = (dx*dx + dy*dy <= 28*28)
                
                # Create smile curve
                in_smile = (dy > 2 and abs(dx) < 20 and abs(dy - 10) < 5)
                
                # Create eyes
                in_eye1 = ((dx+10)**2 + (dy-10)**2 <= 5*5)
                in_eye2 = ((dx-10)**2 + (dy-10)**2 <= 5*5)
                
                if inside_circle:
                    icon.put("#FFD700" if not (in_smile or in_eye1 or in_eye2) else "#000000", (x, y))
                    
        root.iconphoto(True, icon)
    except:
        # Skip icon if there's an error
        pass
    
    # Run the app
    app = FaceDetectionApp(root, "Smile Detection App")
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    root.mainloop()

if __name__ == "__main__":
    main()