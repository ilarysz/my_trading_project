from tkinter import *
from Data_Reader import DataHandler


class Application(Frame):
    def __init__(self, master):
        super(Application, self).__init__(master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        Label(self, text='To load the database: ', bg='White', width=40).grid(row=0, column=0, sticky=W)
        self.result = None
        self.result = Text(self, width=60, height=10, wrap=WORD)
        self.result.grid(row=1, column=0, columnspan=4)
        self.result.insert(0.0, "...")
        Button(self, text="Load", command=self.load_from_db, width=20).grid(row=0, column=1, sticky=W)

    def load_from_db(self):
        self.record = None
        self.my_df = None
        self.record = DataHandler()
        self.my_df = self.record.create_df()
        self.result.delete(0.0, END)
        self.result.insert(0.0, self.my_df)


window = Tk()
window.title("Trade Station")
app = Application(window)
window.mainloop()
