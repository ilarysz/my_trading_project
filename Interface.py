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
        self.result = Text(self, width=60, height=5, wrap=WORD)
        self.result.grid(row=1, column=0, columnspan=4)
        self.result.insert(0.0, "...")
        Button(self, text="Load", command=self.load_from_db, width=20).grid(row=0, column=1, sticky=W)
        self.request_data()

    def load_from_db(self):
        self.db_handler = DataHandler()
        self.result.delete(0.0, END)
        self.result.insert(0.0, self.db_handler.create_df(0)) # 0 hard-coded for testing purposes

    def request_data(self):
        self.current_price = Text(self, width=20, height=1, wrap=WORD)
        price_handler = DataHandler()
        self.current_price.insert(0.0, price_handler.read_from_api('pricing', 2, 'pricing')['bid'])
        Label(self, text='Current EUR_USD price', bg='white', width=20).grid(row=4, column=0, sticky=N)
        self.current_price.grid(row=4, column=1, sticky=W)


window = Tk()
window.title("Trade Station")
app = Application(window)
window.mainloop()
