import tkinter as tk
from .canvas import CanvasFrame
from .mouse import CreatingMouse

# Start a new window with canvas graph and creating mouse
if __name__ == "__main__":
    root = tk.Tk()
    
    frame = CanvasFrame(root)
    
    frame.pack(fill="both", expand=True)
    
    # Add creating mouse to the canvas
    cm = CreatingMouse(frame.canvas, frame.canvas.vertices,
                       button="1", modifier="Control")
    
    root.mainloop()