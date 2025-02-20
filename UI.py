import customtkinter as ctk
from tkinter import filedialog, Toplevel, messagebox, simpledialog
import cv2
import numpy as np
from sklearn.decomposition import PCA
from PIL import Image, ImageDraw, ImageTk


# Initialize the main window
root = ctk.CTk()
root.state('zoomed')  # Set the window to full screen
root.title("Proteus")

pseudocolor_flag = False
sharpie_flag = False
power_flag = False
invert_flag = False
blurDivide_flag = False
noiseReduction_flag = False
PCA_flag = False
pseudocolor_count = 0
sharpie_count = 0
power_count = 0
invert_count = 0
blurDivide_count = 0
noiseReduction_count = 0
PCA_count = 0

# Set the appearance mode of the app to 'dark'
ctk.set_appearance_mode("dark")

# Load the logo image
logo_path = "HokuLike Logo.png"  # Replace with the path to your logo image
logo_image = Image.open(logo_path)
logo_image = logo_image.resize((100, 100), Image.LANCZOS)  # Resize the image using LANCZOS filter
logo_photo = ImageTk.PhotoImage(logo_image)


def generate_pseudocolor_effect(image1_path, image2_path):
    image1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    image2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)

    if image1 is None or image2 is None:
        raise ValueError("One or both images could not be loaded.")
    if image1.shape != image2.shape:
        raise ValueError("The images must have the same size.")

    combined_image = cv2.addWeighted(image1, 0.5, image2, 0.5, 0)
    pseudocolor_image = cv2.applyColorMap(combined_image, cv2.COLORMAP_JET)
    return pseudocolor_image


def apply_pseudocolor_to_current_image(current_image):
    pseudocolor_image = cv2.applyColorMap(current_image, cv2.COLORMAP_JET)
    return pseudocolor_image


def pseudocolor():
    global pseudocolor_flag, pseudocolor_count
    pseudocolor_flag = True
    pseudocolor_count += 1

    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def cancel():
        popup.destroy()

    def generate_effect(entry_image1=None, entry_image2=None):
        image1_path = entry_image1.get()
        image2_path = entry_image2.get()
        if image1_path and image2_path:
            try:
                pseudocolor_image = generate_pseudocolor_effect(image1_path, image2_path)
                pseudocolor_image_rgb = cv2.cvtColor(pseudocolor_image, cv2.COLOR_BGR2RGB)
                pseudocolor_image_pil = Image.fromarray(pseudocolor_image_rgb)
                max_width = root.winfo_width() - 40
                max_height = root.winfo_height() - 200
                pseudocolor_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)
                pseudocolor_image_tk = ImageTk.PhotoImage(pseudocolor_image_pil)
                popup.destroy()
                if label.winfo_exists():
                    label.pack_forget()
                result_label.configure(image=pseudocolor_image_tk, text="")
                result_label.image = pseudocolor_image_tk
                result_label.current_image_pil = pseudocolor_image_pil
                create_band_slider()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def create_band_slider():
        if hasattr(pseudocolor, 'band_slider_frame') and pseudocolor.band_slider_frame.winfo_exists():
            pseudocolor.band_slider_frame.destroy()

        pseudocolor.band_slider_frame = ctk.CTkFrame(root)
        pseudocolor.band_slider_frame.place(relx=0.99, rely=0.5, anchor='ne')  # Adjusted position

        pseudocolor.band_slider = ctk.CTkSlider(pseudocolor.band_slider_frame, from_=0, to=3, number_of_steps=3,
                                                orientation='vertical', height=200)
        pseudocolor.band_slider.set(0)
        pseudocolor.band_slider.pack(side='top', pady=10, padx=10)

        pseudocolor.band_slider_label = ctk.CTkLabel(pseudocolor.band_slider_frame,
                                                     text="Band Selection\n0: All Colors\n1: Red\n2: Green\n3: Blue")
        pseudocolor.band_slider_label.pack(side='top', pady=10, padx=10)

        def update_band(value):
            band = int(value)
            if band == 0:
                display_image(result_label.current_image_pil)
            elif band == 1:
                display_image(result_label.current_image_pil, 'red')
            elif band == 2:
                display_image(result_label.current_image_pil, 'green')
            elif band == 3:
                display_image(result_label.current_image_pil, 'blue')

        pseudocolor.band_slider.bind("<ButtonRelease-1>", lambda event: update_band(pseudocolor.band_slider.get()))

    def display_image(image_pil, color_band=None):
        if color_band == 'red':
            band_image = image_pil.copy().convert('RGB')
            bands = band_image.split()
            band_image = Image.merge('RGB', (bands[0], Image.new('L', bands[1].size), Image.new('L', bands[2].size)))
        elif color_band == 'green':
            band_image = image_pil.copy().convert('RGB')
            bands = band_image.split()
            band_image = Image.merge('RGB', (Image.new('L', bands[0].size), bands[1], Image.new('L', bands[2].size)))
        elif color_band == 'blue':
            band_image = image_pil.copy().convert('RGB')
            bands = band_image.split()
            band_image = Image.merge('RGB', (Image.new('L', bands[0].size), Image.new('L', bands[1].size), bands[2]))
        else:
            band_image = image_pil
        band_image_tk = ImageTk.PhotoImage(band_image)
        result_label.configure(image=band_image_tk)
        result_label.image = band_image_tk

    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        try:
            current_image = np.array(result_label.current_image_pil)
            if len(current_image.shape) == 3 and current_image.shape[2] == 3:
                current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2GRAY)
            pseudocolor_image = apply_pseudocolor_to_current_image(current_image)
            pseudocolor_image_pil = Image.fromarray(cv2.cvtColor(pseudocolor_image, cv2.COLOR_BGR2RGB))
            max_width = root.winfo_width() - 40
            max_height = root.winfo_height() - 200
            pseudocolor_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)
            pseudocolor_image_tk = ImageTk.PhotoImage(pseudocolor_image_pil)
            result_label.configure(image=pseudocolor_image_tk, text="")
            result_label.image = pseudocolor_image_tk
            result_label.current_image_pil = pseudocolor_image_pil
            create_band_slider()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    else:
        popup_width = 500
        popup_height = 350
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        popup_x = int((screen_width - popup_width) / 2)
        popup_y = int((screen_height - popup_height) / 2)
        popup = Toplevel(root)
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.title("Upload Images for Pseudocolor Effect")
        popup.attributes("-topmost", True)
        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)
        label_instruction = ctk.CTkLabel(frame, text="Please upload UV and IR images:", font=("Helvetica", 14))
        label_instruction.pack(pady=10)
        frame_inputs = ctk.CTkFrame(frame)
        frame_inputs.pack(pady=10, padx=10, fill="x")
        label_image1 = ctk.CTkLabel(frame_inputs, text="UV Image:")
        label_image1.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        entry_image1 = ctk.CTkEntry(frame_inputs, width=250)
        entry_image1.grid(row=0, column=1, pady=5, padx=5)
        button_browse1 = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image1))
        button_browse1.grid(row=0, column=2, pady=5, padx=5)
        label_image2 = ctk.CTkLabel(frame_inputs, text="IR Image:")
        label_image2.grid(row=1, column=0, pady=5, padx=5, sticky="w")
        entry_image2 = ctk.CTkEntry(frame_inputs, width=250)
        entry_image2.grid(row=1, column=1, pady=5, padx=5)
        button_browse2 = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image2))
        button_browse2.grid(row=1, column=2, pady=5, padx=5)
        frame_actions = ctk.CTkFrame(frame)
        frame_actions.pack(pady=20)
        button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=cancel, width=100)
        button_cancel.grid(row=0, column=0, padx=10)
        button_generate = ctk.CTkButton(frame_actions, text="Generate",
                                        command=lambda: generate_effect(entry_image1, entry_image2), width=100)
        button_generate.grid(row=0, column=1, padx=10)


# Function to create and display the popup window for Sharpie effect
def sharpie_effect(image):
    if not isinstance(image, np.ndarray):
        raise ValueError("Invalid image input. Must be a numpy array or path.")

    # Ensure the image is loaded correctly
    if image is None:
        raise ValueError("Image could not be loaded.")

    # Apply the Sharpie effect
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
    sharpie_image = 255 - binary

    return sharpie_image


# Function to create and display the popup window for the Sharpie effect
def sharpie():
    global sharpie_flag,sharpie_count
    sharpie_flag = True
    sharpie_count += 1

    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def generate_effect(entry_image=None):
        image_path = entry_image.get()
        try:
            if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
                current_image = np.array(result_label.current_image_pil)
                current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)
                sharpie_image = sharpie_effect(current_image)
            else:
                image = cv2.imread(image_path)
                if image is None:
                    raise ValueError("Image could not be loaded.")
                sharpie_image = sharpie_effect(image)

            sharpie_image_rgb = cv2.cvtColor(sharpie_image, cv2.COLOR_GRAY2RGB)
            sharpie_image_pil = Image.fromarray(sharpie_image_rgb)

            max_width = root.winfo_width() - 40
            max_height = root.winfo_height() - 200
            sharpie_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

            sharpie_image_tk = ImageTk.PhotoImage(sharpie_image_pil)

            popup.destroy()

            if label.winfo_exists():
                label.pack_forget()

            result_label.configure(image=sharpie_image_tk, text="")
            result_label.image = sharpie_image_tk
            result_label.current_image_pil = sharpie_image_pil

        except Exception as e:
            messagebox.showerror("Error", str(e))

    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        current_image = np.array(result_label.current_image_pil)
        current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)
        sharpie_image = sharpie_effect(current_image)

        sharpie_image_rgb = cv2.cvtColor(sharpie_image, cv2.COLOR_GRAY2RGB)
        sharpie_image_pil = Image.fromarray(sharpie_image_rgb)

        max_width = root.winfo_width() - 40
        max_height = root.winfo_height() - 200
        sharpie_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

        sharpie_image_tk = ImageTk.PhotoImage(sharpie_image_pil)

        if label.winfo_exists():
            label.pack_forget()

        result_label.configure(image=sharpie_image_tk, text="")
        result_label.image = sharpie_image_tk
        result_label.current_image_pil = sharpie_image_pil
    else:
        popup_width = 500
        popup_height = 250
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        popup_x = int((screen_width - popup_width) / 2)
        popup_y = int((screen_height - popup_height) / 2)

        popup = Toplevel(root)
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.title("Upload Image for Sharpie Effect")
        popup.attributes("-topmost", True)

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)

        label_instruction = ctk.CTkLabel(frame, text="Please upload an image:", font=("Helvetica", 14))
        label_instruction.pack(pady=10)

        frame_inputs = ctk.CTkFrame(frame)
        frame_inputs.pack(pady=10, padx=10, fill="x")

        label_image = ctk.CTkLabel(frame_inputs, text="Image:")
        label_image.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        entry_image = ctk.CTkEntry(frame_inputs, width=250)
        entry_image.grid(row=0, column=1, pady=5, padx=5)
        button_browse = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image))
        button_browse.grid(row=0, column=2, pady=5, padx=5)

        frame_actions = ctk.CTkFrame(frame)
        frame_actions.pack(pady=20)

        button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=popup.destroy, width=100)
        button_cancel.grid(row=0, column=0, padx=10)

        button_generate = ctk.CTkButton(frame_actions, text="Generate", command=lambda: generate_effect(entry_image),
                                        width=100)
        button_generate.grid(row=0, column=1, padx=10)


# Function to raise image to a given power
def raise_image_to_power(image_path, power):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image at {image_path} could not be loaded.")

    image_float = image.astype(np.float32) / 255.0
    image_power = np.power(image_float, power)
    image_power = np.clip(image_power * 255, 0, 255).astype(np.uint8)

    return image_power


# Function for partial inversion
def partial_inversion(image_path, alpha):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Image at {image_path} could not be loaded.")

    # Invert the image using bitwise NOT
    inverted_image = cv2.bitwise_not(image)

    # Blend the original and inverted images
    output_image = cv2.addWeighted(image, 1 - alpha, inverted_image, alpha, 0)

    return output_image


def power():
    global power_flag,power_count
    power_flag = True
    power_count+= 1

    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def cancel():
        popup.destroy()

    def generate_effect():
        image_path = entry_image.get()
        power_value = entry_power.get()
        if image_path and power_value:
            try:
                power_value = float(power_value)
                if power_value < 0:
                    raise ValueError("Power must be a positive number.")

                power_image = raise_image_to_power(image_path, power_value)

                # Convert the processed image to PIL format for displaying in Tkinter
                power_image_rgb = cv2.cvtColor(power_image, cv2.COLOR_BGR2RGB)
                power_image_pil = Image.fromarray(power_image_rgb)

                # Resize the image to fit within the main window
                max_width = root.winfo_width() - 40  # Leave some padding
                max_height = root.winfo_height() - 300  # Leave some padding for the buttons
                power_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

                power_image_tk = ImageTk.PhotoImage(power_image_pil)

                # Close the popup
                popup.destroy()

                # Remove the welcome label if it exists
                if label.winfo_exists():
                    label.pack_forget()

                # Display the power effect image in the main window
                result_label.configure(image=power_image_tk, text="")
                result_label.image = power_image_tk
                result_label.current_image_pil = power_image_pil  # Save the PIL image for rotation

                # Center the image below the top frame
                result_label.pack(pady=20)

            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))

    # Check if there is a current image displayed
    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        try:
            # Convert the current PIL image to OpenCV format
            current_image = np.array(result_label.current_image_pil)
            current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)

            # Prompt for power value
            power_value = simpledialog.askfloat("Input", "Please enter a power value (positive number):", minvalue=0.0)
            if power_value is not None:
                power_image = np.power(current_image / 255.0, power_value) * 255.0
                power_image = np.clip(power_image, 0, 255).astype(np.uint8)

                # Convert the processed image to PIL format for displaying in Tkinter
                power_image_pil = Image.fromarray(cv2.cvtColor(power_image, cv2.COLOR_BGR2RGB))

                # Resize the image to fit within the main window
                max_width = root.winfo_width() - 40  # Leave some padding
                max_height = root.winfo_height() - 300  # Leave some padding for the buttons
                power_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

                power_image_tk = ImageTk.PhotoImage(power_image_pil)

                # Display the power effect image in the main window
                result_label.configure(image=power_image_tk, text="")
                result_label.image = power_image_tk
                result_label.current_image_pil = power_image_pil  # Save the PIL image for rotation

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

    else:
        # Calculate the position to center the popup window
        popup_width = 500
        popup_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        popup_x = int((screen_width - popup_width) / 2)
        popup_y = int((screen_height - popup_height) / 2)

        popup = Toplevel(root)
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.title("Upload Image for Power Effect")
        popup.attributes("-topmost", True)

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)

        label_instruction = ctk.CTkLabel(frame, text="Please upload an image and enter a power value:",
                                         font=("Helvetica", 14))
        label_instruction.pack(pady=10)

        frame_inputs = ctk.CTkFrame(frame)
        frame_inputs.pack(pady=10, padx=10, fill="x")

        label_image = ctk.CTkLabel(frame_inputs, text="Image:")
        label_image.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        entry_image = ctk.CTkEntry(frame_inputs, width=250)
        entry_image.grid(row=0, column=1, pady=5, padx=5)
        button_browse = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image))
        button_browse.grid(row=0, column=2, pady=5, padx=5)

        label_power = ctk.CTkLabel(frame_inputs, text="Power:")
        label_power.grid(row=1, column=0, pady=5, padx=5, sticky="w")
        entry_power = ctk.CTkEntry(frame_inputs, width=250)
        entry_power.grid(row=1, column=1, pady=5, padx=5)

        frame_actions = ctk.CTkFrame(frame)
        frame_actions.pack(pady=20)

        button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=cancel, width=100)
        button_cancel.grid(row=0, column=0, padx=10)

        button_generate = ctk.CTkButton(frame_actions, text="Generate", command=generate_effect, width=100)
        button_generate.grid(row=0, column=1, padx=10)


def invert():
    global invert_flag, invert_count
    invert_flag = True
    invert_count += 1

    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def cancel():
        popup.destroy()

    def generate_effect():
        image_path = entry_image.get()
        alpha_value = entry_alpha.get()
        if image_path and alpha_value:
            try:
                alpha_value = float(alpha_value)
                if not (0 <= alpha_value <= 1):
                    raise ValueError("Alpha must be between 0 and 1.")

                inverted_image = partial_inversion(image_path, alpha_value)

                # Convert the processed image to PIL format for displaying in Tkinter
                inverted_image_pil = Image.fromarray(cv2.cvtColor(inverted_image, cv2.COLOR_BGR2RGB))

                # Resize the image to fit within the main window
                max_width = root.winfo_width() - 40  # Leave some padding
                max_height = root.winfo_height() - 300  # Leave some padding for the buttons
                inverted_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

                inverted_image_tk = ImageTk.PhotoImage(inverted_image_pil)

                # Close the popup
                popup.destroy()

                # Remove the welcome label if it exists
                if label.winfo_exists():
                    label.pack_forget()

                # Display the inverted effect image in the main window
                result_label.configure(image=inverted_image_tk, text="")
                result_label.image = inverted_image_tk
                result_label.current_image_pil = inverted_image_pil  # Save the PIL image for rotation

                # Center the image below the top frame
                result_label.pack(pady=20)

            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))

    # Check if there is a current image displayed
    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        try:
            # Convert the current PIL image to OpenCV format
            current_image = np.array(result_label.current_image_pil)
            current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)

            # Prompt for alpha value
            alpha_value = simpledialog.askfloat("Input", "Please enter an alpha value (0 to 1):", minvalue=0.0,
                                                maxvalue=1.0)
            if alpha_value is not None:
                inverted_image = cv2.bitwise_not(current_image)
                combined_image = cv2.addWeighted(current_image, 1 - alpha_value, inverted_image, alpha_value, 0)

                # Convert the processed image to PIL format for displaying in Tkinter
                combined_image_pil = Image.fromarray(cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB))

                # Resize the image to fit within the main window
                max_width = root.winfo_width() - 40  # Leave some padding
                max_height = root.winfo_height() - 300  # Leave some padding for the buttons
                combined_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

                combined_image_tk = ImageTk.PhotoImage(combined_image_pil)

                # Display the inverted effect image in the main window
                result_label.configure(image=combined_image_tk, text="")
                result_label.image = combined_image_tk
                result_label.current_image_pil = combined_image_pil  # Save the PIL image for rotation

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

    else:
        # Calculate the position to center the popup window
        popup_width = 500
        popup_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        popup_x = int((screen_width - popup_width) / 2)
        popup_y = int((screen_height - popup_height) / 2)

        popup = Toplevel(root)
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.title("Upload Image for Partial Inversion")
        popup.attributes("-topmost", True)

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)

        label_instruction = ctk.CTkLabel(frame, text="Please upload an image and enter an alpha value:",
                                         font=("Helvetica", 14))
        label_instruction.pack(pady=10)

        frame_inputs = ctk.CTkFrame(frame)
        frame_inputs.pack(pady=10, padx=10, fill="x")

        label_image = ctk.CTkLabel(frame_inputs, text="Image:")
        label_image.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        entry_image = ctk.CTkEntry(frame_inputs, width=250)
        entry_image.grid(row=0, column=1, pady=5, padx=5)
        button_browse = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image))
        button_browse.grid(row=0, column=2, pady=5, padx=5)

        label_alpha = ctk.CTkLabel(frame_inputs, text="Alpha:")
        label_alpha.grid(row=1, column=0, pady=5, padx=5, sticky="w")
        entry_alpha = ctk.CTkEntry(frame_inputs, width=250)
        entry_alpha.grid(row=1, column=1, pady=5, padx=5)

        frame_actions = ctk.CTkFrame(frame)
        frame_actions.pack(pady=20)

        button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=cancel, width=100)
        button_cancel.grid(row=0, column=0, padx=10)

        button_generate = ctk.CTkButton(frame_actions, text="Generate", command=generate_effect, width=100)
        button_generate.grid(row=0, column=1, padx=10)


def rotateRight():
    if result_label.image:
        # Rotate the image to the right by 90 degrees
        rotated_image = result_label.current_image_pil.rotate(-90, expand=True)
        rotated_image_tk = ImageTk.PhotoImage(rotated_image)

        # Update the displayed image
        result_label.configure(image=rotated_image_tk)
        result_label.image = rotated_image_tk
        result_label.current_image_pil = rotated_image  # Save the rotated image for further rotations


def rotateLeft():
    if result_label.image:
        # Rotate the image to the left by 90 degrees
        rotated_image = result_label.current_image_pil.rotate(90, expand=True)
        rotated_image_tk = ImageTk.PhotoImage(rotated_image)

        # Update the displayed image
        result_label.configure(image=rotated_image_tk)
        result_label.image = rotated_image_tk
        result_label.current_image_pil = rotated_image  # Save the rotated image for further rotations


def save():
    if result_label.image:
        # Get the current image from the label
        image = result_label.current_image_pil

        # Ask the user to choose a file path to save the image
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg")

        # Save the image to the chosen file path
        image.save(file_path)
        print("Image saved successfully.")


        # Save metadata to a text file
        metadata_file_path = file_path.replace(".jpg", ".txt")
        with open(metadata_file_path, "w") as metadata_file:
            metadata_file.write("Technical\n")
            metadata_file.write("System Manufacturer: \n")
            metadata_file.write("Lights used: \n")
            metadata_file.write("Name of photographer: \n")
            metadata_file.write("Name of processor: \n")
            metadata_file.write("\n")
            metadata_file.write("Object\n")
            metadata_file.write("Name (if any): \n")
            metadata_file.write("Shelfmark: \n")
            metadata_file.write("Material: \n")
            metadata_file.write("Institution/owner: \n")
            metadata_file.write("\n")

            # Write processes used and their counts
            processes_used = []
            if pseudocolor_count > 0:
                processes_used.append(f"Pseudocolor x{pseudocolor_count}")
            if sharpie_count > 0:
                processes_used.append(f"Sharpie x{sharpie_count}")
            if power_count > 0:
                processes_used.append(f"Power x{power_count}")
            if invert_count > 0:
                processes_used.append(f"Invert x{invert_count}")
            if blurDivide_count > 0:
                processes_used.append(f"Blur & Divide x{blurDivide_count}")
            if noiseReduction_count > 0:
                processes_used.append(f"Noise Reduction x{noiseReduction_count}")
            if PCA_count > 0:
                processes_used.append(f"PCA x{PCA_count}")

            # Write the processes and their counts to the metadata file
            metadata_file.write("Processes used: " + ", ".join(processes_used) + "\n")

        print("Metadata saved successfully.")
    else:
        print("No image to save.")

def clear():
    global invert_flag, pseudocolor_flag, sharpie_flag, power_flag, blurDivide_flag, noiseReduction_flag, PCA_flag

    # Reset all flags
    invert_flag = False
    pseudocolor_flag = False
    sharpie_flag = False
    power_flag = False
    blurDivide_flag = False
    noiseReduction_flag = False
    PCA_flag = False
    pseudocolor_count = 0
    sharpie_count = 0
    power_count = 0
    invert_count = 0
    blurDivide_count = 0
    noiseReduction_count = 0
    PCA_count = 0

    # Remove the image from the result_label
    result_label.configure(image='', text="")
    result_label.image = None
    result_label.current_image_pil = None

    # Show the welcome label
    if not label.winfo_ismapped():
        label.pack(pady=20)


def blur_and_divide(image, blur_value):
    global blurDivide_flag, blurDivide_count
    blurDivide_flag = True
    blurDivide_count += 1
    # Apply Gaussian blur to the image
    blurred_image = cv2.GaussianBlur(image, (blur_value, blur_value), 0)

    # Convert the images to float32 for precision during division
    original_float = image.astype(np.float32)
    blurred_float = blurred_image.astype(np.float32)

    # Avoid division by zero by adding a small epsilon to the blurred image
    epsilon = 1e-10
    blurred_float = np.clip(blurred_float, epsilon, None)

    # Divide the original image by the blurred image
    divided_image = original_float / blurred_float

    # Normalize the resulting image to the range [0, 255]
    divided_image_normalized = cv2.normalize(divided_image, None, 0, 255, cv2.NORM_MINMAX)

    # Convert back to uint8
    divided_image_uint8 = divided_image_normalized.astype(np.uint8)

    # Apply histogram equalization to enhance contrast
    if len(divided_image_uint8.shape) == 2:  # Grayscale image
        equalized_image = cv2.equalizeHist(divided_image_uint8)
    else:  # Color image
        equalized_image = cv2.cvtColor(divided_image_uint8, cv2.COLOR_BGR2YCrCb)
        channels = cv2.split(equalized_image)
        cv2.equalizeHist(channels[0], channels[0])
        equalized_image = cv2.merge(channels)
        equalized_image = cv2.cvtColor(equalized_image, cv2.COLOR_YCrCb2BGR)

    return blurred_image, divided_image_uint8, equalized_image


def blur_and_divide_effect():
    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def cancel():
        popup.destroy()

    def generate_effect():
        image_path = entry_image.get()
        if image_path:
            try:
                original_image = cv2.imread(image_path)
                if original_image is None:
                    raise ValueError(f"Image at {image_path} could not be loaded.")

                blur_value = 15  # You can adjust the blur value as needed
                blurred_image, divided_image, equalized_image = blur_and_divide(original_image, blur_value)

                # Convert the processed image to PIL format for displaying in Tkinter
                equalized_image_rgb = cv2.cvtColor(equalized_image, cv2.COLOR_BGR2RGB)
                equalized_image_pil = Image.fromarray(equalized_image_rgb)

                # Resize the image to fit within the main window
                max_width = root.winfo_width() - 40  # Leave some padding
                max_height = root.winfo_height() - 200  # Leave some padding for the buttons
                equalized_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

                equalized_image_tk = ImageTk.PhotoImage(equalized_image_pil)

                # Close the popup
                popup.destroy()

                # Remove the welcome label if it exists
                if label.winfo_exists():
                    label.pack_forget()

                # Display the equalized image in the main window
                result_label.configure(image=equalized_image_tk, text="")
                result_label.image = equalized_image_tk
                result_label.current_image_pil = equalized_image_pil  # Save the PIL image for rotation

            except ValueError as e:
                print(e)

    # Check if there is a current image displayed
    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        # Convert the current PIL image to OpenCV format
        current_image = np.array(result_label.current_image_pil)
        current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)

        # Apply the effect to the current image
        blur_value = 15  # You can adjust the blur value as needed
        blurred_image, divided_image, equalized_image = blur_and_divide(current_image, blur_value)

        # Convert the processed image to PIL format for displaying in Tkinter
        equalized_image_rgb = cv2.cvtColor(equalized_image, cv2.COLOR_BGR2RGB)
        equalized_image_pil = Image.fromarray(equalized_image_rgb)

        # Resize the image to fit within the main window
        max_width = root.winfo_width() - 40  # Leave some padding
        max_height = root.winfo_height() - 200  # Leave some padding for the buttons
        equalized_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

        equalized_image_tk = ImageTk.PhotoImage(equalized_image_pil)

        # Display the equalized image in the main window
        result_label.configure(image=equalized_image_tk, text="")
        result_label.image = equalized_image_tk
        result_label.current_image_pil = equalized_image_pil  # Save the PIL image for rotation

    else:
        # Calculate the position to center the popup window
        popup_width = 500
        popup_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        popup_x = int((screen_width - popup_width) / 2)
        popup_y = int((screen_height - popup_height) / 2)

        popup = Toplevel(root)
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.title("Upload Image for Blur and Divide Effect")
        popup.attributes("-topmost", True)

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)

        label_instruction = ctk.CTkLabel(frame, text="Please upload an image:", font=("Helvetica", 14))
        label_instruction.pack(pady=10)

        frame_inputs = ctk.CTkFrame(frame)
        frame_inputs.pack(pady=10, padx=10, fill="x")

        label_image = ctk.CTkLabel(frame_inputs, text="Image:")
        label_image.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        entry_image = ctk.CTkEntry(frame_inputs, width=250)
        entry_image.grid(row=0, column=1, pady=5, padx=5)
        button_browse = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image))
        button_browse.grid(row=0, column=2, pady=5, padx=5)

        frame_actions = ctk.CTkFrame(frame)
        frame_actions.pack(pady=20)

        button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=cancel, width=100)
        button_cancel.grid(row=0, column=0, padx=10)

        button_generate = ctk.CTkButton(frame_actions, text="Generate", command=generate_effect, width=100)
        button_generate.grid(row=0, column=1, padx=10)


def pca_transform(image_uv_path, image_lime_path, image_ir_path):
    global PCA_flag, PCA_count
    PCA_flag = False
    PCA_count += 1
    # Load the three images with effects
    image_uv = cv2.imread(image_uv_path)
    image_lime = cv2.imread(image_lime_path)
    image_ir = cv2.imread(image_ir_path)

    # Define the effects colors
    effects = {'UV': [0, 0, 255], 'Lime': [0, 255, 0], 'IR': [255, 0, 0]}

    # Initialize an array for the combined image (assuming all images have the same size)
    combined_image = np.zeros_like(image_uv)

    # Apply effects and combine images
    for effect, color in effects.items():
        if effect == 'UV':
            image_effect = cv2.addWeighted(image_uv, 0.5, np.full(image_uv.shape, color, dtype=np.uint8), 0.5, 0)
        elif effect == 'Lime':
            image_effect = cv2.addWeighted(image_lime, 0.5, np.full(image_lime.shape, color, dtype=np.uint8), 0.5, 0)
        elif effect == 'IR':
            image_effect = cv2.addWeighted(image_ir, 0.5, np.full(image_ir.shape, color, dtype=np.uint8), 0.5, 0)

        # Add the effect to the combined image
        combined_image = cv2.add(combined_image, image_effect)

    # Perform PCA on the combined image
    pca = PCA(n_components=1)  # Keep 1 principal component
    combined_image_flat = combined_image.reshape(-1, 1)
    components = pca.fit_transform(combined_image_flat)

    # Reshape the transformed components back to the original image shape
    transformed_image = components.reshape(combined_image.shape)

    # Scale the transformed image components to the range [0, 255]
    transformed_image = cv2.normalize(transformed_image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

    return transformed_image


def pca_effect():
    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def cancel():
        popup.destroy()

    def generate_effect():
        image_uv_path = entry_image_uv.get()
        image_lime_path = entry_image_lime.get()
        image_ir_path = entry_image_ir.get()
        if image_uv_path and image_lime_path and image_ir_path:
            try:
                transformed_image = pca_transform(image_uv_path, image_lime_path, image_ir_path)

                # Convert the processed image to PIL format for displaying in Tkinter
                transformed_image_pil = Image.fromarray(transformed_image)

                # Resize the image to fit within the main window
                max_width = root.winfo_width() - 40  # Leave some padding
                max_height = root.winfo_height() - 200  # Leave some padding for the buttons
                transformed_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

                transformed_image_tk = ImageTk.PhotoImage(transformed_image_pil)

                # Close the popup
                popup.destroy()

                # Remove the welcome label if it exists
                if label.winfo_exists():
                    label.pack_forget()

                # Display the PCA transformed image in the main window
                result_label.configure(image=transformed_image_tk, text="")
                result_label.image = transformed_image_tk
                result_label.current_image_pil = transformed_image_pil  # Save the PIL image for rotation

                # Disable the PCA button
                button_PCA.configure(state='disabled')

            except ValueError as e:
                print(e)

    # Calculate the position to center the popup window
    popup_width = 500
    popup_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    popup_x = int((screen_width - popup_width) / 2)
    popup_y = int((screen_height - popup_height) / 2)

    popup = Toplevel(root)
    popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
    popup.title("Upload Images for PCA Effect")
    popup.attributes("-topmost", True)

    frame = ctk.CTkFrame(popup)
    frame.pack(fill="both", expand=True)

    label_instruction = ctk.CTkLabel(frame, text="Please upload your images:", font=("Helvetica", 14))
    label_instruction.pack(pady=10)

    frame_inputs = ctk.CTkFrame(frame)
    frame_inputs.pack(pady=10, padx=10, fill="x")

    label_image_uv = ctk.CTkLabel(frame_inputs, text="Image 1:")
    label_image_uv.grid(row=0, column=0, pady=5, padx=5, sticky="w")
    entry_image_uv = ctk.CTkEntry(frame_inputs, width=250)
    entry_image_uv.grid(row=0, column=1, pady=5, padx=5)
    button_browse_uv = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image_uv))
    button_browse_uv.grid(row=0, column=2, pady=5, padx=5)

    label_image_lime = ctk.CTkLabel(frame_inputs, text="Image 2:")
    label_image_lime.grid(row=1, column=0, pady=5, padx=5, sticky="w")
    entry_image_lime = ctk.CTkEntry(frame_inputs, width=250)
    entry_image_lime.grid(row=1, column=1, pady=5, padx=5)
    button_browse_lime = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image_lime))
    button_browse_lime.grid(row=1, column=2, pady=5, padx=5)

    label_image_ir = ctk.CTkLabel(frame_inputs, text="Image 3:")
    label_image_ir.grid(row=2, column=0, pady=5, padx=5, sticky="w")
    entry_image_ir = ctk.CTkEntry(frame_inputs, width=250)
    entry_image_ir.grid(row=2, column=1, pady=5, padx=5)
    button_browse_ir = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image_ir))
    button_browse_ir.grid(row=2, column=2, pady=5, padx=5)

    frame_actions = ctk.CTkFrame(frame)
    frame_actions.pack(pady=20)

    button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=cancel, width=100)
    button_cancel.grid(row=0, column=0, padx=10)

    button_generate = ctk.CTkButton(frame_actions, text="Generate", command=generate_effect, width=100)
    button_generate.grid(row=0, column=1, padx=10)


def reduce_noise(image_input, kernel_size=5, sigma=1.0):
    global noiseReduction_flag, noiseReduction_count
    noiseReduction_flag = True
    noiseReduction_count += 1

    # Check if the input is a string (file path) or an image array
    if isinstance(image_input, str):
        # Read the image from the path
        image = cv2.imread(image_input)
        if image is None:
            raise ValueError("Image not found or path is incorrect")
    elif isinstance(image_input, np.ndarray):
        # Use the image array directly
        image = image_input
    else:
        raise ValueError("Invalid input type. Expected a file path or an image array.")

    # Convert the image from BGR to RGB if it was read from a file
    if isinstance(image_input, str):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Apply Gaussian blur
    denoised_image = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)

    return denoised_image


def noise_effect():
    def open_file(entry):
        file_path = filedialog.askopenfilename(parent=popup)
        if file_path:
            entry.configure(state='normal')
            entry.delete(0, ctk.END)
            entry.insert(0, file_path)
            entry.configure(state='readonly')

    def cancel():
        if popup:
            popup.destroy()

    def generate_effect(image_path=None):
        try:
            if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
                # Use the current displayed image
                current_image = np.array(result_label.current_image_pil)
                current_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)
                transformed_image = reduce_noise(current_image)
            else:
                if not image_path:
                    raise ValueError("No image provided.")
                uploaded_image = cv2.imread(image_path)
                transformed_image = reduce_noise(uploaded_image)

            # Convert the processed image to PIL format for displaying in Tkinter
            transformed_image_pil = Image.fromarray(cv2.cvtColor(transformed_image, cv2.COLOR_BGR2RGB))

            # Resize the image to fit within the main window
            max_width = root.winfo_width() - 40  # Leave some padding
            max_height = root.winfo_height() - 200  # Leave some padding for the buttons
            transformed_image_pil.thumbnail((max_width, max_height), Image.LANCZOS)

            transformed_image_tk = ImageTk.PhotoImage(transformed_image_pil)

            # Close the popup if it exists
            if 'popup' in locals():
                popup.destroy()

            # Remove the welcome label if it exists
            if label.winfo_exists():
                label.pack_forget()

            # Display the noise-reduced image in the main window
            result_label.configure(image=transformed_image_tk, text="")
            result_label.image = transformed_image_tk
            result_label.current_image_pil = transformed_image_pil  # Save the PIL image for rotation

        except Exception as e:
            messagebox.showerror("Error", str(e))

    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        # Directly apply noise reduction if an image is already displayed
        generate_effect()
    else:
        # Calculate the position to center the popup window
        popup_width = 500
        popup_height = 350
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        popup_x = int((screen_width - popup_width) / 2)
        popup_y = int((screen_height - popup_height) / 2)

        popup = Toplevel(root)
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.title("Upload Image for Noise Reduction Effect")
        popup.attributes("-topmost", True)

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True)

        label_instruction = ctk.CTkLabel(frame, text="Please upload your image:", font=("Helvetica", 14))
        label_instruction.pack(pady=10)

        frame_inputs = ctk.CTkFrame(frame)
        frame_inputs.pack(pady=10, padx=10, fill="x")

        label_image_uv = ctk.CTkLabel(frame_inputs, text="Image:")
        label_image_uv.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        entry_image_uv = ctk.CTkEntry(frame_inputs, width=250)
        entry_image_uv.grid(row=0, column=1, pady=5, padx=5)
        button_browse_uv = ctk.CTkButton(frame_inputs, text="Browse", command=lambda: open_file(entry_image_uv))
        button_browse_uv.grid(row=0, column=2, pady=5, padx=5)

        frame_actions = ctk.CTkFrame(frame)
        frame_actions.pack(pady=20)

        button_cancel = ctk.CTkButton(frame_actions, text="Cancel", command=cancel, width=100)
        button_cancel.grid(row=0, column=0, padx=10)

        button_generate = ctk.CTkButton(frame_actions, text="Generate", command=lambda: generate_effect(entry_image_uv.get()), width=100)
        button_generate.grid(row=0, column=1, padx=10)
# Load and resize the magnifying glass image
magnifying_glass_image_path = "magnifying-glass.png"
magnifying_glass_image = Image.open(magnifying_glass_image_path)
magnifying_glass_image = magnifying_glass_image.resize((20, 20), Image.LANCZOS)
magnifying_glass_image_tk = ImageTk.PhotoImage(magnifying_glass_image)

# Load and resize the highlighting tool image
highlighting_tool_image_path = "highlighter.png"
highlighting_tool_image = Image.open(highlighting_tool_image_path)
highlighting_tool_image = highlighting_tool_image.resize((20, 20), Image.LANCZOS)
highlighting_tool_image_tk = ImageTk.PhotoImage(highlighting_tool_image)
# Function to enable/disable magnifying glass tool

# Function to enable/disable magnifying glass tool
def enable_magnifying_glass():
    if magnifying_glass_enabled.get():
        magnifying_glass_enabled.set(False)
        print("Magnifying glass tool disabled")
        reset_image()
    else:
        magnifying_glass_enabled.set(True)
        highlighting_tool_enabled.set(False)
        print("Magnifying glass tool enabled")

# Function to enable/disable highlighting tool
def enable_highlighting_tool():
    if highlighting_tool_enabled.get():
        highlighting_tool_enabled.set(False)
        print("Highlighting tool disabled")
        reset_image()
    else:
        highlighting_tool_enabled.set(True)
        magnifying_glass_enabled.set(False)
        print("Highlighting tool enabled")

# Function to reset the image to its original state
def reset_image():
    if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
        original_image_tk = ImageTk.PhotoImage(result_label.current_image_pil)
        result_label.configure(image=original_image_tk)
        result_label.image = original_image_tk





# Function to handle mouse motion for magnifying glass tool
def magnify(event):
    if magnifying_glass_enabled.get():
        zoom_factor = 2
        x, y = event.x, event.y
        if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
            img = result_label.current_image_pil.copy()
            width, height = img.size

            # Calculate the cropping box, keeping it within image boundaries
            crop_width, crop_height = width // zoom_factor, height // zoom_factor
            left = max(0, min(x - crop_width // 2, width - crop_width))
            top = max(0, min(y - crop_height // 2, height - crop_height))
            right = left + crop_width
            bottom = top + crop_height

            # Crop and resize to achieve the zoom effect
            img = img.crop((left, top, right, bottom))
            img = img.resize((width, height), Image.LANCZOS)
            zoomed_image_tk = ImageTk.PhotoImage(img)
            result_label.configure(image=zoomed_image_tk)
            result_label.image = zoomed_image_tk


# Function to handle mouse click and drag for highlighting tool
def highlight(event):
    if highlighting_tool_enabled.get():
        x, y = event.x, event.y
        if hasattr(result_label, 'current_image_pil') and result_label.current_image_pil is not None:
            img = result_label.current_image_pil.copy()
            draw = ImageDraw.Draw(img)
            size = 5
            draw.ellipse((x - size, y - size, x + size, y + size), fill="yellow", outline="yellow")
            highlighted_image_tk = ImageTk.PhotoImage(img)
            result_label.configure(image=highlighted_image_tk)
            result_label.image = highlighted_image_tk
            result_label.current_image_pil_temp = img  # Update the PIL image


# Variables to store the current state of the tools
magnifying_glass_enabled = ctk.BooleanVar(value=False)
highlighting_tool_enabled = ctk.BooleanVar(value=False)

# Create a frame for the tools on the lower right side
tools_frame = ctk.CTkFrame(root, width=100, height=60)
tools_frame.place(relx=1.0, rely=1.0, anchor='se')

# Add magnifying glass button
magnifying_glass_button = ctk.CTkButton(tools_frame, image=magnifying_glass_image_tk, text="", command=enable_magnifying_glass, width=30, height=30)
magnifying_glass_button.pack(side='right', padx=5, pady=5)

# Add highlighting tool button
highlighting_tool_button = ctk.CTkButton(tools_frame, image=highlighting_tool_image_tk, text="", command=enable_highlighting_tool, width=30, height=30)
highlighting_tool_button.pack(side='right', padx=5, pady=5)


# Create a frame for the top section
top_frame = ctk.CTkFrame(root)
top_frame.pack(side="top", fill="x", pady=10)

# Add the logo to the top-left corner
logo_label = ctk.CTkLabel(top_frame, image=logo_photo, text="")
logo_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

# Create buttons for effects
buttons_frame = ctk.CTkFrame(top_frame)
buttons_frame.grid(row=0, column=1, padx=10)

button_pseudocolor = ctk.CTkButton(buttons_frame, text="Pseudocolor", command=pseudocolor, width=100, height=40)
button_sharpie = ctk.CTkButton(buttons_frame, text="Sharpie", command=sharpie, width=100, height=40)
button_power = ctk.CTkButton(buttons_frame, text="Power", command=power, width=100, height=40)
button_invert = ctk.CTkButton(buttons_frame, text="Invert", command=invert, width=100, height=40)
button_rotateRight = ctk.CTkButton(buttons_frame, text="Rotate Right", command=rotateRight, width=100, height=40)
button_rotateLift = ctk.CTkButton(buttons_frame, text="Rotate Left", command=rotateLeft, width=100, height=40)
button_blurDivide = ctk.CTkButton(buttons_frame, text="Blur & Divide", command=blur_and_divide_effect, width=100, height=40)
button_noiseReduction = ctk.CTkButton(buttons_frame, text="Noise Reduction", command=noise_effect, width=100, height=40)
button_PCA = ctk.CTkButton(buttons_frame, text="PCA", command=pca_effect, width=100, height=40)

button_pseudocolor.grid(row=0, column=0, padx=5)
button_sharpie.grid(row=0, column=1, padx=5)
button_power.grid(row=0, column=2, padx=5)
button_invert.grid(row=0, column=3, padx=5)
button_rotateRight.grid(row=0, column=4, padx=5)
button_rotateLift.grid(row=0, column=5, padx=5)
button_blurDivide.grid(row=0, column=6, padx=5)
button_noiseReduction.grid(row=0, column=7, padx=5)
button_PCA.grid(row=0, column=8, padx=5)

# Create buttons for save and import
button_save = ctk.CTkButton(top_frame, text="Save", command=save, width=100, height=40)
button_clear = ctk.CTkButton(top_frame, text="Clear", command=clear, width=100, height=40)

button_save.grid(row=0, column=2, padx=5, sticky="e")
button_clear.grid(row=0, column=3, padx=5, sticky="e")

top_frame.grid_columnconfigure(0, weight=0)  # Logo column
top_frame.grid_columnconfigure(1, weight=1)  # Buttons column
top_frame.grid_columnconfigure(2, weight=0)  # Save and Import column

# Create a welcome label in the center
label = ctk.CTkLabel(root, text="Welcome to Proteus", font=("Helvetica", 24))
label.pack(pady=20)

# Create a label to display the effect image
result_label = ctk.CTkLabel(root, text="")
# Bind mouse events to the result label for the tools

result_label.bind("<Motion>", magnify)
result_label.bind("<B1-Motion>", highlight)
result_label.pack(pady=20)

# Start the main loop
root.mainloop()
