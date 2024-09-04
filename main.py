import tkinter as tk  # Import the Tkinter library for creating GUI applications
from tkinter import ttk  # Import the ttk module for themed widgets like Treeview
import PIL.Image  # Import the Image class from PIL (Pillow) for image processing
import PIL.ImageTk  # Import the ImageTk class to convert PIL images to Tkinter images
import cv2  # Import OpenCV for computer vision tasks
import webbrowser  # Import the webbrowser module to open links in the web browser
from pyzbar.pyzbar import decode  # Import the decode function from pyzbar to decode barcodes
import numpy as np  # Import NumPy for numerical operations, including image array manipulation
import pymsgbox  # Import pymsgbox for pop-up messages

# Initialize the camera capture object globally
cap = None

# Initialize a global set to keep track of seen barcodes
seen_barcodes = set()

def decode_barcodes_over_feed(image):
    """
    Function to decode barcodes from the image and update the Treeview with new barcodes.
    """
    global seen_barcodes  # Use the global set to track barcodes that have been seen

    # Convert the PIL image to a NumPy array for OpenCV processing
    image_np = np.array(image)

    # Decode barcodes from the given image using pyzbar
    barcodes = decode(image_np)
    
    # Iterate over all detected barcodes
    for i, barcode in enumerate(barcodes):
        # Decode the barcode data to a string
        barcode_data = barcode.data.decode("utf-8")

        # Extract the coordinates and dimensions of the barcode bounding box
        (x, y, w, h) = barcode.rect

        # Check if the barcode data has already been added to the Treeview
        if barcode_data in seen_barcodes:
            # Draw a rectangle around the barcode on the image (already seen)
            cv2.rectangle(image_np, (x, y), (x + w, y + h), (225, 225, 225), 2)
            # Put the barcode data as text above the rectangle
            cv2.putText(image_np, barcode_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (225, 225, 225), 2)
            continue  # Skip this barcode if it has already been seen

        # Add the barcode data to the seen set to avoid processing it again
        seen_barcodes.add(barcode_data)
        # Automatically open the barcode data (assuming it's a URL) in the default web browser
        webbrowser.open(barcode_data)

        # Draw a rectangle around the barcode on the image
        cv2.rectangle(image_np, (x, y), (x + w, y + h), (225, 225, 225), 2)

        # Get the type of the barcode (e.g., QR Code, Code128)
        barcode_type = barcode.type

        # Prepare the text to display (barcode data and type)
        text = f"{barcode_data} ({barcode_type})"
        
        # Put the text above the rectangle on the image
        cv2.putText(image_np, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (225, 225, 225), 2)

        # Insert the barcode data into the Treeview with an ID and the decoded data
        tree.insert("", tk.END, text=i, values=(i+1, barcode_data))

    # Convert the NumPy array back to a PIL image and return it for display in Tkinter
    return PIL.Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))

def cam_feed(label):
    """
    Function to start the camera feed and continuously update the image on the Tkinter label.
    """
    global cap

    # Stop the previous feed update loop by releasing the camera if it's already running
    if cap is not None:
        cap.release()

    # Create a new VideoCapture object based on the selected camera source
    cap = cv2.VideoCapture(camera_source.get())

    # Setting the camera properties before capturing frames
    cap.set(3, 450)  # Set the width of the video capture to 450 pixels
    cap.set(4, 450)  # Set the height of the video capture to 450 pixels
    cap.set(5, 120)  # Set the frame rate of the video capture to 120 FPS
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))  # Set the codec to MJPG

    def update_frame():
        """
        Inner function to update the camera feed frame by frame.
        """
        ret, frame = cap.read()  # Capture a frame from the camera
        frame = cv2.flip(frame, 1)  # Flip the frame horizontally (mirror effect)

        if ret:
            # Convert the BGR frame to RGB for display in Tkinter
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert the RGB frame to a PIL image
            img = PIL.Image.fromarray(rgb)

            # Decode barcodes over the feed and update the image with any detected barcodes
            img = decode_barcodes_over_feed(img)

            # Convert the PIL image to an ImageTk object for display in Tkinter
            imgTk = PIL.ImageTk.PhotoImage(img)
            label.imgtk = imgTk  # Keep a reference to avoid garbage collection
            label.configure(image=imgTk)  # Update the label to display the new image

        # Schedule the update_frame function to be called again after 10 milliseconds
        label.after(10, update_frame)

    # Start the update loop
    update_frame()

def take_picture():
    """
    Function to capture a single image from the camera feed and save it as a file.
    """
    global cap

    if cap is None or not cap.isOpened():
        pymsgbox.alert('Please start the video feed first.', 'Warning')  # Alert user if the camera feed is not running
    else:
        ret, frame = cap.read()  # Capture a frame from the camera
        frame = cv2.flip(frame, 1)  # Flip the frame horizontally (mirror effect)

        if ret:
            # Save the captured frame as a JPEG file
            cv2.imwrite('captured_image.jpg', frame)
            print("Image captured and saved as 'captured_image.jpg'")
        else:
            pymsgbox.alert('Failed to capture image.', 'Error')

def detect_code(image="captured_image.jpg"):
    """
    Function to detect barcodes in a saved image file and update the Treeview with detected barcodes.
    """
    global cap

    # Release the camera if it's running to avoid conflict with loading a saved image
    if cap is not None:
        cap.release()

    # Clear the tree data before inserting new data
    for item in tree.get_children():
        tree.delete(item)
    
    try:
        # Open the image file using PIL
        img = PIL.Image.open(image)
        
        # Convert the PIL image to a NumPy array for OpenCV processing
        img_np = np.array(img)
        
        # Check if the image is valid (non-empty and of proper shape)
        if img_np.size == 0:
            raise ValueError("The image is empty or corrupted.")
        
    except (FileNotFoundError, ValueError) as e:
        # Handle the case where the file is not found or corrupted
        pymsgbox.alert(f"Error: {str(e)}")
        return

    # Convert the PIL image to a NumPy array for OpenCV processing
    img_np = np.array(img)

    # Decode barcodes from the image using pyzbar
    decoded_image = decode(cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY))

    if len(decoded_image) == 0:
        # If no barcodes are detected, insert a message into the Treeview
        tree.insert("", tk.END, text="n/a", values=(1, "No barcodes detected"))

    for i, barcode in enumerate(decoded_image):
        # Extract the coordinates and dimensions of the barcode bounding box
        (x, y, w, h) = barcode.rect

        # Draw a rectangle around the detected barcode
        cv2.rectangle(img_np, (x, y), (x + w, y + h), (0, 0, 255), 4)

        # Decode the barcode data and type
        data = barcode.data.decode("utf-8")

        # Insert the barcode data into the Treeview
        tree.insert("", tk.END, text=i, values=(i+1, data))
        
    # Convert the NumPy array back to a PIL image for display in Tkinter
    img_pil = PIL.Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))
    img_tk = PIL.ImageTk.PhotoImage(image=img_pil)
    
    # Update the label with the new image
    cam_label.imgtk = img_tk
    cam_label.configure(image=img_tk)

def select_link(event):
    """
    Function to open a link in the web browser when a barcode is selected from the Treeview.
    """
    # Get the selected item ID
    selected_item = tree.selection()[0]

    # Get the values associated with the selected item
    values  = tree.item(selected_item, "values")

    # Extract the actual data (link) from the values tuple
    link = values[1]

    if link.startswith("https:"):
        # Open the link in the default web browser
        webbrowser.open(link)
    else:
        # Confirm with the user whether they want to open the non-link item
        response = pymsgbox.confirm('The item selected is not a link. Do you still want to open it?', 'Confirmation')
        if response == 'OK':
            webbrowser.open(link)
        else:
            print("User chose to cancel")

# Main Tkinter application window
root = tk.Tk()
root.geometry("800x500")  # Set the window size
root.title("Barcode detection")

camera_source = tk.IntVar(value=0)  # Default to 0 (built-in camera)

# Frame for displaying the camera feed
cam_frame = tk.Frame(root)
cam_frame.place(x=10, y=10, width=450, height=450)

# Label to display the camera feed
cam_label = tk.Label(cam_frame, text="Display")
cam_label.pack()

# Button to capture a picture from the camera feed
take_picture_button = tk.Button(root, text="Take a Picture", command=take_picture, bg="blue", fg="white")
take_picture_button.place(x=470, y=10, width=120, height=40)

# Button to detect barcodes from a saved image
detect_code_button = tk.Button(root, text="Detect Code", command=lambda: detect_code(), bg="green", fg="white")
detect_code_button.place(x=470, y=60, width=120, height=40)

# Button to start the camera feed
show_feed = tk.Button(root, text="Start feed", command=lambda: cam_feed(cam_label), bg="blue", fg="white")
show_feed.place(x=470, y=110, width=120, height=40)

# Button to exit the application
exit_button = tk.Button(root, text="Exit", command=root.destroy, bg="red", fg="white")
exit_button.place(x=470, y=160, width=120, height=40)

# Radio buttons to select the camera source (built-in or external webcam)
def_cam = tk.Radiobutton(root, text="Built-in Camera (opens faster)", variable=camera_source, value=0)
def_cam.place(x=470, y=210)
web_cam = tk.Radiobutton(root, text="Webcam (opens slower)", variable=camera_source, value=1)
web_cam.place(x=470, y=240)

# Treeview to display the detected barcodes
tree = ttk.Treeview(root)
tree["columns"] = ("Id", "Data")
tree.column("#0", width=0, stretch=tk.NO)  # Hide the first column
tree.column("Id", width=5)
tree.column("Data", width=200)
tree.heading("Id", text="Id")
tree.heading("Data", text="Data")

# Bind the Treeview selection event to the select_link function
tree.bind("<<TreeviewSelect>>", select_link)
tree.place(x=470, y=270, width=320, height=225)

# Start the Tkinter event loop
root.mainloop()

# Release the capture and close windows when the program ends
if cap is not None:
    cap.release()

cv2.destroyAllWindows  # Clean up OpenCV resources
