import sys
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit,QMessageBox
)

class STLTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Text STL Generator")
        self.setGeometry(200, 200, 400, 200)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input for the name
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter name in Hebrew")
        layout.addWidget(QLabel("Text to convert:"))
        layout.addWidget(self.name_input)

        # Font file selector
        self.font_label = QLabel("No font selected")
        self.font_btn = QPushButton("Select Font")
        self.font_btn.clicked.connect(self.load_font)
        layout.addWidget(self.font_label)
        layout.addWidget(self.font_btn)

        # Input count of Letters
        self.letter_count = QLineEdit(self)
        self.letter_count.setPlaceholderText("Enter count of text")
        layout.addWidget(QLabel("count of letters:"))
        layout.addWidget(self.letter_count)

        # Generate STL button
        self.generate_btn = QPushButton("Generate STL")
        self.generate_btn.clicked.connect(self.run_generate)
        layout.addWidget(self.generate_btn)

        self.setLayout(layout)

    def load_font(self):
        font_path, _ = QFileDialog.getOpenFileName(self, "Select Font File", "", "Font Files (*.ttf *.otf)")
        if font_path:
            self.font_label.setText(font_path)
            self.font_path = font_path

    def generate_stl(self):
        text = self.name_input.text()
        font_path = getattr(self, 'font_path', None)
        count_letters = self.letter_count.text()

        if text and font_path and count_letters:
            self.run_generate()
        else:
            print("Please enter text, count of letters and select a font.")

    def run_generate(self):
        text = self.name_input.text()
        font_path = self.font_label.text()
        count_letters = self.letter_count.text()
        if not text:
            QMessageBox.warning(self, "Input Error", "Please enter text to convert.")
            return
        if "No font selected" in font_path:
            font_path = None  # Font is optional
        if not count_letters:
            QMessageBox.warning(self, "Input Error", "Please enter count of letters.")
            return
        if not count_letters.isnumeric:
            QMessageBox.warning(self, "Input Error", "Please enter number.")
            return
        command = [
            "blender", 
            "--background", 
            "--python", 
            ".\\generate_stl.py", 
            "--", 
            text, 
            font_path,
            count_letters
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
            # Print the output and error
            print("Output:")
            print(result.stdout)
            print("\nErrors:")
            print(result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")
            print("Error output:")
            print(e.stderr)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = STLTool()
    window.show()
    sys.exit(app.exec_())
