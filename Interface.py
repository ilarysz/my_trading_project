from tkinter import *
from Data_Reader import DataHandler
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt


class Application(Frame):
    def __init__(self, master):
        super(Application, self).__init__(master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        Label(self, text='To load the database: ', bg='White', width=40).grid(row=0, column=0, sticky=W)
        self.result = None
        self.result = Text(self, width=150, height=5, wrap=WORD)
        self.result.grid(row=1, column=0, columnspan=12)
        self.result.insert(0.0, "...")
        Button(self, text="Load", command=self.load_from_db, width=20).grid(row=0, column=1, sticky=W)
        self.create_plot()

    def load_from_db(self):
        self.db_handler = DataHandler()
        self.result.delete(0.0, END)
        self.result.insert(0.0, self.db_handler.create_df(0)) # 0 hard-coded for testing purposes

    def request_data(self, request_type='pricing', pair_choice=0, streaming_type='pricing'):
        data_handler = DataHandler()
        requested_data = data_handler.read_from_api(request_type, pair_choice, streaming_type)
        return requested_data

    def create_plot(self):
        # /// most of the data have set values, interface level modifications to be added
        # gather history data as dataframe from api
        history_data = self.request_data(request_type='history', pair_choice=1) # last parameter shall be static
        # prepare plot with predefined parameters
        f = Figure(figsize=(5, 5), dpi=100)
        a = f.add_subplot(111)
        a.plot([1, 2, 3, 4, 5, 6, 7, 8], [5, 6, 1, 3, 8, 9, 3, 5])

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=6, column=0)


window = Tk()
window.title("Trade Station")
app = Application(window)
window.mainloop()
