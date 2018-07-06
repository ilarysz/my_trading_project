from tkinter import *
from Data_Reader import DataHandler
from Trading_Engine import Request


class Application(Frame):
    def __init__(self, master):
        super(Application, self).__init__(master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        Label(self, text='To load the database: ', bg='White', width=40).grid(row=0, column=0, sticky=W)
        self.result = None
        self.result = Text(self, width=60, height=5, wrap=WORD)
        self.result.grid(row=1, column=0, columnspan=4)
        self.result.insert(0.0, "...")
        Button(self, text="Load", command=self.load_from_db, width=20).grid(row=0, column=1, sticky=W)
        self.request_data()

    def load_from_db(self):
        self.record = None
        self.my_df = None
        self.record = DataHandler()
        self.my_df = self.record.create_df()
        self.result.delete(0.0, END)
        self.result.insert(0.0, self.my_df)

    def request_data(self):
        self.current_price = Text(self, width=20, height=1, wrap=WORD)
        r = Request()
        r_output = r.perform_request()
        self.current_price.insert(0.0, r_output)
        Label(self, text='Current EUR_USD price', bg='white', width=20).grid(row=4, column=0, sticky=N)
        self.current_price.grid(row=4, column=1, sticky=W)


window = Tk()
window.title("Trade Station")
app = Application(window)
window.mainloop()
