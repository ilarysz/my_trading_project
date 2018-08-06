from Data_Reader import DataHandler

import pandas as pd
import numpy as np

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib import pyplot as plt

import tkinter as tk
from tkinter import ttk

from datetime import datetime

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Verdana", 10)
SMALL_FONT = ("Verdana", 8)
style.use("ggplot")

f = Figure()
a = f.add_subplot(111)
major_pairs = ("AUD_USD", "EUR_CHF", "EUR_USD", "GBP_JPY", "GBP_USD", "NZD_USD", "USD_CAD", "USD_CHF", "USD_JPY")

# Set variables that will carry the chart defaults
user_pair_choice = 0
user_candles_count_choice = 150
user_granularity_choice = 'H1'
chart_indicator = ['name', 0]
bottom_indicator = ['name', 0, 0, 0]
animation_status = True


def set_indicators(chart=None, bottom=None):

    if chart:
        if chart == "sma":
            indicator_setter = tk.Tk()
            indicator_setter.wm_title("Configure")
            label1 = ttk.Label(indicator_setter, text="Set the period for moving average")
            label1.pack(padx=10, pady=5)
            entry1 = ttk.Entry(indicator_setter)
            entry1.insert(0, 14)
            entry1.pack(padx=10, fill='x')
            entry1.focus_set()

            def callback():
                global chart_indicator
                chart_indicator[0] = 'sma'
                chart_indicator[1] = entry1.get()
                print("Indicator {} set with period of {}".format(chart_indicator[0], chart_indicator[1]))

                indicator_setter.destroy()

            button1 = ttk.Button(indicator_setter, text="Ok", width=10, command=callback)
            button1.pack(padx=10, pady=5, fill='x')

            indicator_setter.mainloop()

        elif chart == 'ema':
            indicator_setter = tk.Tk()
            indicator_setter.wm_title("Configure")
            label1 = ttk.Label(indicator_setter, text="Set the period for moving average")
            label1.pack(padx=10, pady=5)
            entry1 = ttk.Entry(indicator_setter)
            entry1.insert(0, 14)
            entry1.pack(padx=10, fill='x')
            entry1.focus_set()

            def callback():
                global chart_indicator
                chart_indicator[0] = 'ema'
                chart_indicator[1] = entry1.get()
                print("Indicator {} set with period of {}".format(chart_indicator[0], chart_indicator[1]))

                indicator_setter.destroy()

            button1 = ttk.Button(indicator_setter, text="Ok", width=10, command=callback)
            button1.pack(padx=10, pady=5, fill='x')

            indicator_setter.mainloop()

    if bottom:
        if bottom == 'rsi':
            # Show the window to let user choose RSI period
            rsi_setter = tk.Tk()
            rsi_setter.wm_title("Configure RSI")

            label1 = tk.Label(rsi_setter, text="Set the period for rsi", font=NORM_FONT)
            label1.pack(side='top', pady=10, padx=10)
            entry1 = tk.Entry(rsi_setter)
            entry1.insert(0, 7)
            entry1.pack()
            entry1.focus_set()

            def callback():
                global bottom_indicator
                bottom_indicator[0] = bottom
                bottom_indicator[1] = entry1.get()
                print(f"Indicator set to {bottom_indicator[0]} with period of {bottom_indicator[1]}")
                rsi_setter.destroy()

            button1 = ttk.Button(rsi_setter, text="Ok", width=10, command=callback)
            button1.pack()
            rsi_setter.mainloop()

        elif bottom == 'macd':
            macd_setter = tk.Tk()
            macd_setter.wm_title("Configure MACD")

            label0 = ttk.Label(macd_setter, text="Set the periods for MACD")
            label0.grid(row=0, column=0, columnspan=2)

            label1 = ttk.Label(macd_setter, text='Faster MA')
            label1.grid(row=1, column=0, pady=5, padx=5)
            entry1 = ttk.Entry(macd_setter)
            entry1.insert(0, 12)
            entry1.grid(row=1, column=1, pady=5, padx=5)
            entry1.focus_set()

            label2 = ttk.Label(macd_setter, text='Slower MA')
            label2.grid(row=2, column=0, pady=5, padx=5)
            entry2 = ttk.Entry(macd_setter)
            entry2.insert(0, 26)
            entry2.grid(row=2, column=1, pady=5, padx=5)

            label3 = ttk.Label(macd_setter, text='Signal line')
            label3.grid(row=3, column=0, pady=5, padx=5)
            entry3 = ttk.Entry(macd_setter)
            entry3.insert(0, 9)
            entry3.grid(row=3, column=1, pady=5, padx=5)

            def callback():
                global bottom_indicator
                bottom_indicator[0] = bottom
                bottom_indicator[1] = entry1.get()
                bottom_indicator[2] = entry2.get()
                bottom_indicator[3] = entry3.get()

                print("Indicator set to {indicator} with following parameters: {first_param}, {second_param}, "
                      "{third_param}".format(indicator=bottom_indicator[0], first_param=bottom_indicator[1],
                                             second_param=bottom_indicator[2], third_param=bottom_indicator[3]))

                macd_setter.destroy()

            button1 = ttk.Button(macd_setter ,text="Ok", command=callback)
            button1.grid(row=5, column=0, pady=5, columnspan=2)

            macd_setter.mainloop()

def animation_changer(status):
    global animation_status
    if status == 'on':
        animation_status = True
    elif status == 'off':
        animation_status = False


def tf_changer(tf):
    global user_granularity_choice
    user_granularity_choice = tf


def window_capacity_changer(window):
    global user_candles_count_choice

    # Calculate hours in current timeframe
    hours_in_tf = None
    if user_granularity_choice == 'H1':
        hours_in_tf = 1
    elif user_granularity_choice == 'H4':
        hours_in_tf = 4
    elif user_granularity_choice == 'D':
        hours_in_tf = 24
    elif user_granularity_choice == 'W':
        hours_in_tf = 168
    else:
        raise LookupError("Given TF value not found!")

    if int(round(window / hours_in_tf, 0)) > 1000:
        popupmsg(msg="Number of downloaded candles exceeds 1000!")
        return 1

    # Knowing number of hours in window and time frame, candles counter can be derived
    user_candles_count_choice = int(round(window / hours_in_tf, 0))


def pair_choice_changer(chosen_pair):
    global user_pair_choice
    user_pair_choice = chosen_pair


def popupmsg(msg, title="Error"):
    popup = tk.Tk()

    def leave_window():
        popup.destroy()

    popup.wm_title(title)
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    popup_button1 = ttk.Button(popup, text="Ok, close the window", command=leave_window)
    popup_button1.pack()

    popup.mainloop()

def create_bottom_indicator():
    if bottom_indicator == 'macd':
        pass
    elif bottom_indicator == 'rsi':
        pass


def create_chart_indicator():
    if chart_indicator == 'sma':
        pass
    elif chart_indicator == 'ema':
        pass


def animate(i):
    """For animation function purposes. It reloads the data basing on the given time frame"""
    global animation_status
    if animation_status:
        data_handler = DataHandler()
        history_data = data_handler.read_from_api(request_type='history', pair_choice=user_pair_choice,
                                                  candles_count=user_candles_count_choice+bottom_indicator[2]+
                                                                chart_indicator[1],
                                                  set_granularity=user_granularity_choice, streaming_type="pricing")
        a.clear()
        history_data['time'] = np.array(history_data['time']).astype("datetime64[s]")
        pricing_dates = history_data['time'].tolist()
        a.plot(pricing_dates, [float(x) for x in history_data.iloc[:user_candles_count_choice]['c']], color='#00A3E0',
               label=major_pairs[user_pair_choice], ls='-')
        a.set_title("Chart of %s \n Last price: %s" % (major_pairs[user_pair_choice], history_data['c'][149]))


class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.iconbitmap(self, default="chart.ico")
        tk.Tk.wm_title(self, "Trading Station")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save settings", command=lambda: popupmsg("Not supported yet!"))
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        change_tf = tk.Menu(menubar, tearoff=1)
        # Probably needed number of candles to load variable
        change_tf.add_command(label="H1", command=lambda: tf_changer('H1'))
        change_tf.add_command(label="H4", command=lambda: tf_changer('H4'))
        change_tf.add_command(label="D1", command=lambda: tf_changer('D'))
        change_tf.add_command(label="W1", command=lambda: tf_changer('W'))
        menubar.add_cascade(label="Time frame", menu=change_tf)

        window_capacity = tk.Menu(menubar, tearoff=1)
        window_capacity.add_command(label="One Week", command=lambda: window_capacity_changer(7*24))
        window_capacity.add_command(label="One Month", command=lambda: window_capacity_changer(31*24))
        window_capacity.add_command(label="Half a year", command=lambda: window_capacity_changer(365/2*24))
        window_capacity.add_command(label="One year", command=lambda: window_capacity_changer(365*24))
        window_capacity.add_command(label="Five years", command=lambda: window_capacity_changer(5*365*24))
        menubar.add_cascade(label="Capacity", menu=window_capacity)

        pair_choice = tk.Menu(menubar, tearoff=1)
        pair_choice.add_command(label='AUD_USD', command=lambda: pair_choice_changer(0))
        pair_choice.add_command(label='EUR_CHF', command=lambda: pair_choice_changer(1))
        pair_choice.add_command(label='EUR_USD', command=lambda: pair_choice_changer(2))
        pair_choice.add_command(label='GBP_JPY', command=lambda: pair_choice_changer(3))
        pair_choice.add_command(label='GBP_USD', command=lambda: pair_choice_changer(4))
        pair_choice.add_command(label='NZD_USD', command=lambda: pair_choice_changer(5))
        pair_choice.add_command(label='USD_CAD', command=lambda: pair_choice_changer(6))
        pair_choice.add_command(label='USD_CHF', command=lambda: pair_choice_changer(7))
        pair_choice.add_command(label='USD_JPY', command=lambda: pair_choice_changer(8))
        menubar.add_cascade(label="Pair", menu=pair_choice)

        indicators = tk.Menu(menubar, tearoff=1)
        indicators.add_command(label="RSI", command=lambda: set_indicators(bottom='rsi'))
        indicators.add_command(label="MACD", command=lambda: set_indicators(bottom='macd'))
        indicators.add_separator()
        indicators.add_command(label="SMA", command=lambda: set_indicators(chart='sma'))
        indicators.add_command(label="EMA", command=lambda: set_indicators(chart='ema'))
        menubar.add_cascade(label='Indicators', menu=indicators)

        start_stop = tk.Menu(menubar, tearoff=1)
        start_stop.add_command(label="Start", command=lambda: animation_changer(status='on'))
        start_stop.add_command(label="Stop", command=lambda: animation_changer(status='off'))
        menubar.add_cascade(label="Auto-update", menu=start_stop)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}

        for F in (StartPage, PageOne, PageTwo):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, control):
        frame = self.frames[control]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Home Page", font=LARGE_FONT)
        label.pack(padx=10, pady=10)
        # Using lambda function to prevent from immediate initialization
        button1 = ttk.Button(self, text="Static chart", command=lambda: controller.show_frame(PageOne))
        button1.pack()
        button2 = ttk.Button(self, text="Dynamic chart", command=lambda: controller.show_frame(PageTwo))
        button2.pack()


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Static chart page", font=LARGE_FONT)
        label.pack(padx=10, pady=10)
        # Using lambda function to prevent from immediate initialization
        button1 = ttk.Button(self, text="Return to Home Page", command=lambda: controller.show_frame(StartPage))
        button1.pack()
        # load data that are about to be plotted (only first time the chart is shown) later only the last candle
        # is updated with usage of animate function
        self.create_chart()

    def create_chart(self, load_from='api', user_pair_choice=0):
        data_handler = DataHandler()
        if (load_from == 'api'):
            self.history_data = data_handler.read_from_api(request_type='history', pair_choice=user_pair_choice,
                                              candles_count=150, set_granularity='H1', streaming_type="pricing")
        elif (load_from == 'db'):
            self.history_data = data_handler.create_df(choice=user_pair_choice)
        else:
            raise ValueError("Invalid command!")

        f = Figure(figsize=(5, 5), dpi=100)
        a = f.add_subplot(111)
        a.plot_date(
            [datetime.strptime(x, '%Y-%m-%d %H:%M').strftime('%m-%d %H:%M') for x in self.history_data['time'][139:]],
            [float(x) for x in self.history_data.iloc[139:]['c']])

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        # canvas.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Dynamic chart page', font=LARGE_FONT)
        label.pack(padx=10, pady=10)
        button1 = ttk.Button(self, text='Return to Home Page', command=lambda: controller.show_frame(StartPage))
        button1.pack()
        self.create_chart()

    def create_chart(self):
        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        # canvas.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


app = Application()
app.geometry("1280x720")
ani = animation.FuncAnimation(f, animate, interval=5000)
app.mainloop()
