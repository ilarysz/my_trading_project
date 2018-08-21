from Data_Reader import DataHandler

import pandas as pd
import numpy as np

import matplotlib

# matplotlib.use must be before any imports from matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib import pyplot as plt
from matplotlib import ticker as mpl_ticker
from matplotlib import dates as mpl_dates
import mpl_finance

import tkinter as tk
from tkinter import ttk

from datetime import datetime

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Verdana", 10)
SMALL_FONT = ("Verdana", 8)
style.use("ggplot")

# f must be called at the top as it will be used by the animate function (that do not belong to any object)
# and as well must be packed by the FigureCanvasTkAgg present in PageTwo to be shown by tkinter
f = plt.figure()
major_pairs = ("AUD_USD", "EUR_CHF", "EUR_USD", "GBP_JPY", "GBP_USD", "NZD_USD", "USD_CAD", "USD_CHF", "USD_JPY")

# Set variables that will carry the chart defaults
user_pair_choice = 0
user_candles_count_choice = 150
user_granularity_choice = 'H1'
chart_indicator = ['name', 0]
bottom_indicator = ['name', 0, 0, 0]
show_volume = 'disable'
animation_status = True


def set_indicators(chart=None, bottom=None, volume=None):
    # Currently program supports to have one bottom and chart indicator at time
    # This function is called from the menu bar
    # Each if statement has to show simple dialog box that allows to customize indicators' periods
    # Highest number is about to be set on second ([1]) position of global variable
    # No separate description as behavior of each is very similar
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

            # After "OK" button is clicked retrieve informations from the entry box, write it to global variables, quit
            def callback():
                global chart_indicator
                chart_indicator[0] = 'sma'
                chart_indicator[1] = int(entry1.get())
                # Send confirmation to console
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
                chart_indicator[1] = int(entry1.get())
                print("Indicator {} set with period of {}".format(chart_indicator[0], chart_indicator[1]))

                indicator_setter.destroy()

            button1 = ttk.Button(indicator_setter, text="Ok", width=10, command=callback)
            button1.pack(padx=10, pady=5, fill='x')

            indicator_setter.mainloop()

        elif chart == 'disable':
            # Restore defaults on global variable
            global chart_indicator
            chart_indicator = ['name', 0]

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
                bottom_indicator[1] = int(entry1.get())
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

            # Slower MA is contained in first place to retain highest numer on [1] in bottom_indicator list
            label1 = ttk.Label(macd_setter, text='Slower MA')
            label1.grid(row=1, column=0, pady=5, padx=5)
            entry1 = ttk.Entry(macd_setter)
            entry1.insert(0, 26)
            entry1.grid(row=1, column=1, pady=5, padx=5)
            entry1.focus_set()

            label2 = ttk.Label(macd_setter, text='Faster MA')
            label2.grid(row=2, column=0, pady=5, padx=5)
            entry2 = ttk.Entry(macd_setter)
            entry2.insert(0, 12)
            entry2.grid(row=2, column=1, pady=5, padx=5)

            label3 = ttk.Label(macd_setter, text='Signal line')
            label3.grid(row=3, column=0, pady=5, padx=5)
            entry3 = ttk.Entry(macd_setter)
            entry3.insert(0, 9)
            entry3.grid(row=3, column=1, pady=5, padx=5)

            def callback():
                global bottom_indicator
                bottom_indicator[0] = bottom
                bottom_indicator[1] = int(entry1.get())
                bottom_indicator[2] = int(entry2.get())
                bottom_indicator[3] = int(entry3.get())

                print("Indicator set to {indicator} with following parameters: {first_param}, {second_param}, "
                      "{third_param}".format(indicator=bottom_indicator[0], first_param=bottom_indicator[1],
                                             second_param=bottom_indicator[2], third_param=bottom_indicator[3]))

                macd_setter.destroy()

            button1 = ttk.Button(macd_setter, text="Ok", command=callback)
            button1.grid(row=5, column=0, pady=5, columnspan=2)

            macd_setter.mainloop()

        elif bottom == 'disable':
            # Restore defaults on the global variable
            global bottom_indicator
            bottom_indicator = ['name', 0, 0, 0]

    if volume:
        global show_volume
        if volume == 'enable':
            show_volume = 'enable'
        elif volume == 'disable':
            show_volume = 'disable'


def animation_changer(status):
    # Animation sometimes cause troubles as it reset any toolbar view modifications
    # Simple if statement in animate function will check for animation_status variable to be "on" or "off"
    global animation_status
    if status == 'on':
        animation_status = True
    elif status == 'off':
        animation_status = False


def tf_changer(tf):
    # Change global variable that has H1/H4/D1/W1 etc. information
    global user_granularity_choice
    user_granularity_choice = tf


def window_capacity_changer(window):
    global user_candles_count_choice

    # Window capactiy takes processes all data on the one hour time frame
    # Calculate hours in current time frame
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

    # More than 1 000 candles cause troubles with API (server return 40x response)
    # SQL can load more candles in future such distinction will be added
    if int(round(window / hours_in_tf, 0)) > 1000:
        popupmsg(msg="Number of downloaded candles exceeds 1000! \n (Indicator data also are counted in.) \n"
                     "Only first 1000 candles will be downloaded.")
        user_candles_count_choice = 1000

    # Knowing number of hours in window and time frame, candles counter can be derived
    user_candles_count_choice = int(round(window / hours_in_tf, 0))


def pair_choice_changer(chosen_pair):
    # Modify global variable that selects the pair to load from API / SQL database
    global user_pair_choice
    user_pair_choice = chosen_pair


def popupmsg(msg, title="Error"):
    # Simple pop-up showing only title, given message and button to close it
    popup = tk.Tk()

    def leave_window():
        popup.destroy()

    popup.wm_title(title)
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    popup_button1 = ttk.Button(popup, text="Ok, close the window", command=leave_window)
    popup_button1.pack()

    popup.mainloop()


def create_bottom_indicator(pricing_data_frame):
    if bottom_indicator[0] == 'macd':
        # Method of calculating MACD: Subtract slower EMA from faster what created MACD Line. Signal line is EMA from
        # the MACD Line. Histogram is supportive and represents difference between MACD Line and signal line
        pricing_data_frame['macd_ema_slow'] = pricing_data_frame['c'].ewm(span=bottom_indicator[1],
                                                                          adjust=False, min_periods=bottom_indicator[1],
                                                                          ignore_na=True).mean()
        pricing_data_frame['macd_ema_fast'] = pricing_data_frame['c'].ewm(span=bottom_indicator[2],
                                                                          adjust=False, min_periods=bottom_indicator[2],
                                                                          ignore_na=True).mean()
        pricing_data_frame['macd_line'] = pricing_data_frame['macd_ema_slow'] - pricing_data_frame['macd_ema_fast']
        pricing_data_frame['signal_line'] = pricing_data_frame['macd_line'].ewm(span=bottom_indicator[3],
                                                                                adjust=False,
                                                                                min_periods=bottom_indicator[3],
                                                                                ignore_na=True).mean()
        pricing_data_frame['histogram'] = pricing_data_frame['macd_line'] - pricing_data_frame['signal_line']
        return pricing_data_frame
    elif bottom_indicator[0] == 'rsi':
        return 0


def create_chart_indicator(pricing_data_frame):
    if chart_indicator[0] == 'sma':
        sma = pricing_data_frame['c'].rolling(chart_indicator[1]).mean()
        return sma
    elif chart_indicator[0] == 'ema':
        # Options allow to show NaN on the head data
        ema = pricing_data_frame['c'].ewm(span=chart_indicator[1], adjust=False, min_periods=chart_indicator[1],
                                          ignore_na=True).mean()
        return ema


def animate(i):
    """For animation function purposes. It reloads the data basing on the given time frame"""
    global animation_status
    global f
    if animation_status:
        data_handler = DataHandler()
        # Candles count takes into account requirement from indicators to have extra data
        # In bottom_indicator the highest number is always stored on [1] position
        history_data = data_handler.read_from_api(request_type='history', pair_choice=user_pair_choice,
                                                  candles_count=user_candles_count_choice + bottom_indicator[1] +
                                                  chart_indicator[1],
                                                  set_granularity=user_granularity_choice, streaming_type="pricing")
        history_data['time'] = np.array(history_data['time']).astype("datetime64[s]")
        pricing_dates = history_data['time'].tolist()
        # Plots exclude by using indexing the extra indicators data that are in the data frame
        if bottom_indicator[1] != 0 and chart_indicator[1] != 0:
            print("Chart with bottom indicator and MA initialized")
            history_data = create_bottom_indicator(history_data)
            chart_indicator_data = create_chart_indicator(history_data)
            # Cut the chart by the highest number from the indicators
            if max(bottom_indicator[1:]) >= max(chart_indicator[1:]):
                # MACD will create even more NaNs due to signal line
                if bottom_indicator[0] == 'macd':
                    cut = max(bottom_indicator[1:3]) + bottom_indicator[3]
                else:
                    cut = bottom_indicator[1]
            else:
                cut = chart_indicator[1]

            # Plotting part
            a1 = plt.subplot2grid((6, 1), (0, 0), 4, 1)
            a1.clear()
            zipped_prices = zip(range(len(pricing_dates[cut:])),  # mpl_dates.date2num(pricing_dates[cut:]),
                                [float(x) for x in history_data.iloc[cut:]['o']],
                                [float(x) for x in history_data.iloc[cut:]['c']],
                                [float(x) for x in history_data.iloc[cut:]['h']],
                                [float(x) for x in history_data.iloc[cut:]['l']])
            mpl_finance.candlestick_ochl(a1, zipped_prices, colordown='red', colorup='green')
            a1.set_title("Chart of %s \nLast price: %s" % (major_pairs[user_pair_choice], history_data.iloc[-1]['c']))
            a1.xaxis.set_visible(False)
            a1.set_ylabel("Price")
            # Plotting moving average
            a1.plot(range(len(pricing_dates[cut:])), chart_indicator_data[cut:])

            # Bottom subplot with indicator data
            a2 = plt.subplot2grid((6, 1), (4, 0), 2, 1, sharex=a1)
            a2.clear()
            if bottom_indicator[0] == 'macd':
                a2.plot(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['macd_line'])
                a2.plot(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['signal_line'])
                a2.fill_between(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['histogram'], 0,
                                interpolate=True, color='grey')
                a2.xaxis.set_major_locator(mpl_ticker.MaxNLocator(16))
                tick_labels = a2.get_xticklabels(which='both')
                for pos, label in enumerate(tick_labels):
                    try:
                        tick_labels[pos] = str(
                            pricing_dates[int(round(pos * (len(pricing_dates) / len(tick_labels)), 0))])[:10]
                    except LookupError:
                        tick_labels[pos] = pricing_dates[-1]
                a2.set_xticklabels(tick_labels)
                for label in a2.xaxis.get_ticklabels():
                    label.set_rotation(30)
                # a2.xaxis.set_major_formatter(mpl_dates.DateFormatter("%Y-%m-%d"))
                a2.set_ylabel("MACD")
            elif bottom_indicator[0] == 'rsi':
                # --- RSI function not prepared
                pass
            else:
                raise RuntimeError("Indicator not defined")

        elif bottom_indicator[1] != 0:
            print("Chart with bottom indicator initialized")
            history_data = create_bottom_indicator(history_data)

            # Chart shall be count by the indicator periods due to NaN of used moving averages in them
            # It is taken into account when downloading data, user receives given time span
            # MACD needs even larger cut due to signal line created on the faster and slower MAs
            if bottom_indicator[0] == 'rsi':
                cut = bottom_indicator[1]
            elif bottom_indicator[0] == 'macd':
                cut = bottom_indicator[1] + bottom_indicator[3]
            else:
                raise RuntimeError("Indicator not defined")

            a1 = plt.subplot2grid((6, 1), (0, 0), 4, 1)
            a1.clear()
            zipped_prices = zip(range(len(pricing_dates[cut:])),  # mpl_dates.date2num(pricing_dates[cut:]),
                                [float(x) for x in history_data.iloc[cut:]['o']],
                                [float(x) for x in history_data.iloc[cut:]['c']],
                                [float(x) for x in history_data.iloc[cut:]['h']],
                                [float(x) for x in history_data.iloc[cut:]['l']])
            mpl_finance.candlestick_ochl(a1, zipped_prices, colordown='red', colorup='green')
            a1.set_title("Chart of %s \nLast price: %s" % (major_pairs[user_pair_choice], history_data.iloc[-1]['c']))
            a1.xaxis.set_visible(False)
            a1.set_ylabel("Price")

            a2 = plt.subplot2grid((6, 1), (4, 0), 2, 1, sharex=a1)
            a2.clear()
            if bottom_indicator[0] == 'macd':
                a2.plot(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['macd_line'])
                a2.plot(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['signal_line'])
                a2.fill_between(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['histogram'], 0,
                                interpolate=True, color='grey')
                a2.xaxis.set_major_locator(mpl_ticker.MaxNLocator(16))
                tick_labels = a2.get_xticklabels(which='both')
                for pos, label in enumerate(tick_labels):
                    try:
                        tick_labels[pos] = str(
                            pricing_dates[int(round(pos * (len(pricing_dates) / len(tick_labels)), 0))])[:10]
                    except LookupError:
                        tick_labels[pos] = pricing_dates[-1]
                a2.set_xticklabels(tick_labels)
                for label in a2.xaxis.get_ticklabels():
                    label.set_rotation(30)
                # a2.xaxis.set_major_formatter(mpl_dates.DateFormatter("%Y-%m-%d"))
                a2.set_ylabel("MACD")
            elif bottom_indicator[0] == 'rsi':
                # --- RSI function not prepared
                pass
            else:
                raise RuntimeError("Indicator not defined")

        elif chart_indicator[1] != 0:
            print("Chart with MA initialized")
            chart_indicator_data = create_chart_indicator(history_data)
            cut = chart_indicator[1]
            a1 = plt.subplot2grid((6, 1), (0, 0), 6, 1)
            a1.clear()
            # Firstly, x axis is created as a integer axis (to force matplotlib to not show weekends)
            zipped_prices = zip(range(len(pricing_dates[cut:])),  # mpl_dates.date2num(pricing_dates),
                                [float(x) for x in history_data.iloc[cut:]['o']],
                                [float(x) for x in history_data.iloc[cut:]['c']],
                                [float(x) for x in history_data.iloc[cut:]['h']],
                                [float(x) for x in history_data.iloc[cut:]['l']])
            # List returned by the function contains tick labels with proper intervals
            # Tick labels are manually substituted with proper dates (strings with the hour part cut)
            # Currently zoom problem occurs (x tick labels does not match)
            a1.xaxis.set_major_locator(mpl_ticker.MaxNLocator(12))
            tick_labels = a1.get_xticklabels(which='both')
            for pos, label in enumerate(tick_labels):
                try:
                    tick_labels[pos] = str(
                        pricing_dates[cut:][int(round(pos * (len(pricing_dates) / len(tick_labels)), 0))])[:10]
                except LookupError:
                    tick_labels[pos] = pricing_dates[cut:][-1]
            a1.set_xticklabels(tick_labels)
            for label in a1.xaxis.get_ticklabels():
                label.set_rotation(30)
            # Library that creates candlesticks is manually added to the program in separate file
            mpl_finance.candlestick_ochl(a1, zipped_prices, colordown='red', colorup='green', width=0.2)
            a1.set_title("Chart of %s \nLast price: %s" % (major_pairs[user_pair_choice], history_data.iloc[-1]['c']))
            a1.set_ylabel("Price")
            a1.plot(range(len(pricing_dates[cut:])), chart_indicator_data[cut:])

        else:
            print("Price only chart initialized")
            cut = 0
            a1 = plt.subplot2grid((6, 1), (0, 0), 6, 1)
            a1.clear()
            # Firstly, x axis is created as a integer axis (to force matplotlib to not show weekends)
            zipped_prices = zip(range(len(pricing_dates)),  # mpl_dates.date2num(pricing_dates),
                                [float(x) for x in history_data['o']],
                                [float(x) for x in history_data['c']],
                                [float(x) for x in history_data['h']],
                                [float(x) for x in history_data['l']])
            # List returned by the function contains tick labels with proper intervals
            # Tick labels are manually substituted with proper dates (strings with the hour part cut)
            # Currently zoom problem occurs (x tick labels does not match)
            a1.xaxis.set_major_locator(mpl_ticker.MaxNLocator(12))
            tick_labels = a1.get_xticklabels(which='both')
            for pos, label in enumerate(tick_labels):
                try:
                    tick_labels[pos] = str(
                        pricing_dates[int(round(pos * (len(pricing_dates) / len(tick_labels)), 0))])[:10]
                except LookupError:
                    tick_labels[pos] = pricing_dates[-1]
            a1.set_xticklabels(tick_labels)
            for label in a1.xaxis.get_ticklabels():
                label.set_rotation(30)
            # Library that creates candlesticks is manually added to the program in separate file
            mpl_finance.candlestick_ochl(a1, zipped_prices, colordown='red', colorup='green', width=0.2)
            a1.set_title("Chart of %s \nLast price: %s" % (major_pairs[user_pair_choice], history_data.iloc[-1]['c']))
            a1.set_ylabel("Price")

        if show_volume == 'enable':
            # Volume plotting lives outside other plotting "ifs"
            # Volume is always overlayed on the main (a1) chart axis
            print('Volume added to chart')
            a1v = a1.twinx()
            a1v.fill_between(range(len(pricing_dates[cut:])), 0,
                             [int(x) for x in history_data.iloc[cut:]['volume']], color="#0000FF", alpha=0.5)
            a1v.set_ylim(0, max(history_data.iloc[cut:]['volume']*3))
            a1v.grid(False)
            a1v.set_ylabel("Volume")


class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_iconbitmap(self, bitmap="chart.ico")
        tk.Tk.wm_title(self, "Trading Station")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Upper option menu bar definition, all of cascades can be teared off, lambda functions prevent from
        # immediate initialization of separate functions that configure global variables used by the animate
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
        window_capacity.add_command(label="One Week", command=lambda: window_capacity_changer(7 * 24))
        window_capacity.add_command(label="One Month", command=lambda: window_capacity_changer(31 * 24))
        window_capacity.add_command(label="Half a year", command=lambda: window_capacity_changer(365 / 2 * 24))
        window_capacity.add_command(label="One year", command=lambda: window_capacity_changer(365 * 24))
        window_capacity.add_command(label="Five years", command=lambda: window_capacity_changer(5 * 365 * 24))
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
        indicators.add_command(label="Disable bottom", command=lambda: set_indicators(bottom='disable'))
        indicators.add_separator()
        indicators.add_command(label="SMA", command=lambda: set_indicators(chart='sma'))
        indicators.add_command(label="EMA", command=lambda: set_indicators(chart='ema'))
        indicators.add_command(label="Disable MA", command=lambda: set_indicators(chart='disable'))
        indicators.add_separator()
        indicators.add_command(label="Show volume", command=lambda: set_indicators(volume='enable'))
        indicators.add_command(label="Hide volume", command=lambda: set_indicators(volume='disable'))
        menubar.add_cascade(label='Indicators', menu=indicators)

        start_stop = tk.Menu(menubar, tearoff=1)
        start_stop.add_command(label="Start", command=lambda: animation_changer(status='on'))
        start_stop.add_command(label="Stop", command=lambda: animation_changer(status='off'))
        menubar.add_cascade(label="Auto-update", menu=start_stop)

        tk.Tk.config(self, menu=menubar)

        # Dictionary containg all pages (Tkinter objects)
        self.frames = {}

        # Each page before adding to dict is initialized with tk.Frame object and placed on the grid
        for F in (StartPage, PageOne, PageTwo):
            # Start Page is passed as the "controller" it will allow to call show_frame method later
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show default page
        self.show_frame(StartPage)

    # Function that allows to change pages (window views}
    def show_frame(self, control):
        frame = self.frames[control]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        # Start page currently only has to show links to other ones and raise them
        # Controller is not passed as it is class Application used only for frame changes
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
        # data_handler is responsible to load data from API and SQL database
        data_handler = DataHandler()
        if load_from == 'api':
            self.history_data = data_handler.read_from_api(request_type='history', pair_choice=user_pair_choice,
                                                           candles_count=150, set_granularity='H1',
                                                           streaming_type="pricing")
        elif load_from == 'db':
            self.history_data = data_handler.create_df(choice=user_pair_choice)
        else:
            raise ValueError("Invalid command!")

        f = Figure(figsize=(5, 5), dpi=100)
        a = f.add_subplot(111)
        a.plot_date(
            [datetime.strptime(x, '%Y-%m-%d %H:%M').strftime('%m-%d %H:%M') for x in self.history_data['time'][139:]],
            [float(x) for x in self.history_data.iloc[139:]['c']])

        # First create object provided by matplotlib library, standard plotting with usage of it
        # And getting widget with subsequent placing on the grid
        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Bottom option bar
        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        # canvas.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) - currently causing troubles


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Dynamic chart page', font=LARGE_FONT)
        label.pack(padx=10, pady=10)
        button1 = ttk.Button(self, text='Return to Home Page', command=lambda: controller.show_frame(StartPage))
        button1.pack()
        self.create_chart()

    def create_chart(self):
        # PageTwo chart is animated and most of it is created in the outer (animate) function

        # First create object provided by matplotlib library, standard plotting with usage of it
        # And getting widget with subsequent placing on the grid
        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Bottom option bar
        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        # canvas.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) - currently causing troubles


# Initialize tk
app = Application()
app.geometry("1280x720")
# Due to use of animation plotting function lives outside any objects
ani = animation.FuncAnimation(f, animate, interval=5000)
app.mainloop()
