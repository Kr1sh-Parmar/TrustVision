# How to Run TrustVision

Follow these steps to set up and run the TrustVision application on your local machine.

## 1. Open the Project Directory
Ensure you are in the root directory of the application:
```bash
cd "semi final"
```

## 2. Set Up a Virtual Environment
It is recommended to use a virtual environment to manage dependencies securely.

**For Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**For Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies
Install all required Python libraries (including Flask, OpenCV, TensorFlow, and Web3):
```bash
pip install -r requirements.txt
```

## 4. Download Required ML Models
The facial recognition feature requires a pre-trained Keras model. Download it by running the included script:
```bash
python download_model.py
```
*(Note: If the download script fails, it will provide you with a manual Google Drive/Kaggle link. Ensure the downloaded model is placed in the `models/` directory as `facenet_keras.h5`.)*

## 5. Install Tesseract OCR (Optional but Recommended)
For the Document Verification (ID/Aadhar card) feature to work fully, you must install Tesseract OCR on your system.
- **Windows**: Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and install it. Ensure the install path is added to your system's Environment Variables.
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

## 6. Start the Application
Run the Flask server:
```bash
python app.py
```

## 7. Access the Dashboard
Open your web browser and navigate to:
**[http://localhost:5000/](http://localhost:5000/)**

---

### Troubleshooting
- **Port 5000 in use**: If the default Flask port is already in use, you can modify the last line in `app.py` to `app.run(debug=True, port=5001)` and navigate to `localhost:5001`.
- **Camera Not Working**: The app uses your default webcam for face registration. If it crashes upon opening the camera, ensure another application (like Zoom or Teams) isn't holding onto the camera feed.
- **ModuleNotFoundError**: Ensure your virtual environment is activated (`(venv)` should appear in your terminal prompt) before running `app.py`.
