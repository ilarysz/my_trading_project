# Built-in libraries
import tkinter as tk
from tkinter import ttk
from datetime import datetime
# Third-party libraries
import pandas as pd
import numpy as np
import webbrowser
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
# Custom packages
from database_methods import DataHandler
import mpl_finance
from api_methods import RequestPricing, RequestInstrument
from analysis_module import IndicatorsCalculator
# Global variables
from shared_variables import major_pairs


# Set font and style
LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Verdana", 10)
SMALL_FONT = ("Verdana", 8)
style.use("ggplot")
# Set variables that will carry the chart defaults
user_pair_choice = 0
user_candles_count_choice = 150
user_granularity_choice = 'H1'
chart_indicator = ['name', 0]
bottom_indicator = ['name', 0, 0, 0]
show_volume = 'disable'
animation_status = True
chart_open = False
first_time = False

# f must be called at the top as it will be used by the animate function (that do not belong to any object)
# and as well must be packed by the FigureCanvasTkAgg present in PageTwo to be shown by tkinter
f = plt.figure()
indicators_calculator = IndicatorsCalculator()


def chart_status(status):
    # Change chart open/close status depending on the command origin
    global chart_open
    global first_time
    chart_open = status
    if chart_open:
        first_time = True


def set_indicators(chart=None, bottom=None, volume=None):
    # Currently program supports to have one bottom and chart indicator at time
    # This function is called from the menu bar
    # Each if statement has to show simple dialog box that allows to customize indicators' periods
    # Highest number is about to be set on second ([1]) position of global variable
    # Behavior of each part of if statements is very similar
    # Chart indicator part
    if chart:
        # Determine the type of chart indicator (currently available: EMA, SMA)
        if chart == "sma":
            # Evoke new window with settings
            indicator_setter = tk.Tk()
            indicator_setter.wm_title("Configure")
            # Allow user to set the period of MA
            # One row of label/entry pair, focus on the entry window
            label1 = ttk.Label(indicator_setter, text="Set the period for moving average")
            label1.pack(padx=10, pady=5)
            entry1 = ttk.Entry(indicator_setter)
            entry1.insert(0, 14)
            entry1.pack(padx=10, fill='x')
            entry1.focus_set()

            # After "OK" button is clicked retrieve information from the entry box, write it to global variables, quit
            def callback():
                global chart_indicator
                chart_indicator[0] = 'sma'
                chart_indicator[1] = int(entry1.get())
                # Send confirmation to console
                print("Indicator {} set with period of {}".format(chart_indicator[0], chart_indicator[1]))

                # Close the window with MA settings
                indicator_setter.destroy()

            # Add button that calls callback method
            button1 = ttk.Button(indicator_setter, text="Ok", width=10, command=callback)
            button1.pack(padx=10, pady=5, fill='x')

            indicator_setter.mainloop()

        elif chart == 'ema':
            # Evoke similar window to that in case of SMA, main differences come with "callback" method
            indicator_setter = tk.Tk()
            indicator_setter.wm_title("Configure")
            label1 = ttk.Label(indicator_setter, text="Set the period for moving average")
            label1.pack(padx=10, pady=5)
            entry1 = ttk.Entry(indicator_setter)
            entry1.insert(0, 14)
            entry1.pack(padx=10, fill='x')
            entry1.focus_set()

            # After "OK" button is clicked retrieve information from the entry box, write it to global variables, quit
            def callback():
                global chart_indicator
                chart_indicator[0] = 'ema'
                chart_indicator[1] = int(entry1.get())

                # Print confirmation to console
                print("Indicator {} set with period of {}".format(chart_indicator[0], chart_indicator[1]))

                # Close the settings window
                indicator_setter.destroy()

            button1 = ttk.Button(indicator_setter, text="Ok", width=10, command=callback)
            button1.pack(padx=10, pady=5, fill='x')

            indicator_setter.mainloop()

        elif chart == 'disable':
            # Restore defaults on global variable
            global chart_indicator
            chart_indicator = ['name', 0]

    # Indicator below the chart
    if bottom:

        if bottom == 'rsi':
            # Show the window to let user choose RSI period
            # As for MAs, the windows construction is very similar and main changes come with the "callback" method
            rsi_setter = tk.Tk()
            rsi_setter.wm_title("Configure RSI")

            label1 = tk.Label(rsi_setter, text="Set the period for rsi", font=NORM_FONT)
            label1.pack(side='top', pady=10, padx=10)
            entry1 = tk.Entry(rsi_setter)
            entry1.insert(0, 7)
            entry1.pack()
            entry1.focus_set()

            # After "OK" button is clicked retrieve information from the entry box, write it to global variables, quit
            def callback():
                global bottom_indicator
                bottom_indicator[0] = bottom
                bottom_indicator[1] = int(entry1.get())

                # Print confirmation to console
                print(f"Indicator set to {bottom_indicator[0]} with period of {bottom_indicator[1]}")

                # Close the settings window
                rsi_setter.destroy()

            button1 = ttk.Button(rsi_setter, text="Ok", width=10, command=callback)
            button1.pack()
            rsi_setter.mainloop()

        elif bottom == 'macd':
            # Show the window to let user choose MACD periods
            # As for MAs, the windows construction is very similar and main changes come with the "callback" method
            macd_setter = tk.Tk()
            macd_setter.wm_title("Configure MACD")

            # Upper label
            label0 = ttk.Label(macd_setter, text="Set the periods for MACD")
            label0.grid(row=0, column=0, columnspan=2)

            # Slower MA is contained in first place to retain highest numer on [1] in bottom_indicator list
            # Prepare series of rows (label/entry) pairs and set the focus the first one
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

            # After "OK" button is clicked retrieve information from the entry box, write it to global variables, quit
            def callback():
                global bottom_indicator
                bottom_indicator[0] = bottom
                bottom_indicator[1] = int(entry1.get())
                bottom_indicator[2] = int(entry2.get())
                bottom_indicator[3] = int(entry3.get())

                # Print confirmation to console
                print("Indicator set to {indicator} with following parameters: {first_param}, {second_param}, "
                      "{third_param}".format(indicator=bottom_indicator[0], first_param=bottom_indicator[1],
                                             second_param=bottom_indicator[2], third_param=bottom_indicator[3]))

                # Close the settings window
                macd_setter.destroy()

            button1 = ttk.Button(macd_setter, text="Ok", command=callback)
            button1.grid(row=5, column=0, pady=5, columnspan=2)

            macd_setter.mainloop()

        elif bottom == 'disable':
            # Restore defaults in the global variable
            global bottom_indicator
            bottom_indicator = ['name', 0, 0, 0]

    if volume:
        # Show volume below the chart. Only switches the variable. It is used by the charting method
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

    # More than 1 000 candles cause troubles with API (server return 40X response)
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

    # Close the window when "Ok" is clicked
    def leave_window():
        popup.destroy()

    # Set the title
    popup.wm_title(title)
    # Prepare and set the Label
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    # Create button that allows to close the window
    popup_button1 = ttk.Button(popup, text="Ok, close the window", command=leave_window)
    popup_button1.pack()

    popup.mainloop()


def animate(i):
    # For animation function purposes. It reloads the data basing on the given time frame
    global f
    if animation_status and chart_open:
        # Candles count takes into account requirement from indicators to have extra data
        # In bottom_indicator the highest number is always stored on [1] position
        # i.e. if MA period is 14 and user request 100 candles, 114 are ultimately downloaded to evade gaps on chart
        api_connector = RequestInstrument()
        history_data = api_connector.perform_request(pair_choice=user_pair_choice,
                                                     candles_count=user_candles_count_choice + bottom_indicator[1] +
                                                                   chart_indicator[1],
                                                     set_granularity=user_granularity_choice)
        history_data['time'] = np.array(history_data['time']).astype("datetime64[s]")
        pricing_dates = history_data['time'].tolist()

        # Plots exclude by using indexing the extra indicators data that are in the data frame
        # If statements check which of indicators are currently initialized
        if bottom_indicator[1] != 0 and chart_indicator[1] != 0:
            print("Chart with bottom indicator and MA initialized")
            # Create bottom indicator basing on the user preferences
            history_data = indicators_calculator.create_bottom_indicator(history_data, bottom_indicator)
            chart_indicator_data = indicators_calculator.create_chart_indicator(history_data, chart_indicator)
            # Cut the chart by the highest number from the indicator periods
            if max(bottom_indicator[1:]) >= max(chart_indicator[1:]):
                # MACD will create even more NaNs due to signal line
                if bottom_indicator[0] == 'macd':
                    cut = max(bottom_indicator[1:3]) + bottom_indicator[3]
                else:
                    cut = bottom_indicator[1]
            else:
                cut = chart_indicator[1]

            # Plotting part
            # 4 rows of grid for main chart, 1 space, 1 indicator chart
            a1 = plt.subplot2grid((6, 1), (0, 0), 4, 1)
            # Clear former chart and plot that with updated pricing
            a1.clear()
            # Separate and convert to floats each pricing column and zip it for candlestick chart
            zipped_prices = zip(range(len(pricing_dates[cut:])),  # mpl_dates.date2num(pricing_dates[cut:]),
                                [float(x) for x in history_data.iloc[cut:]['o']],
                                [float(x) for x in history_data.iloc[cut:]['c']],
                                [float(x) for x in history_data.iloc[cut:]['h']],
                                [float(x) for x in history_data.iloc[cut:]['l']])
            # Plot candles
            mpl_finance.candlestick_ochl(a1, zipped_prices, colordown='red', colorup='green')
            # Chart configuration, title shows chosen pair and last price
            a1.set_title("Chart of %s \nLast price: %s" % (major_pairs[user_pair_choice], history_data.iloc[-1]['c']))
            # Disable axis on the main chart (it will be shown by the bottom indicator)
            a1.xaxis.set_visible(False)
            a1.set_ylabel("Price")
            # Plotting moving average
            a1.plot(range(len(pricing_dates[cut:])), chart_indicator_data[cut:])

            # Bottom subplot with indicator data
            a2 = plt.subplot2grid((6, 1), (4, 0), 2, 1, sharex=a1)
            # Clear former chart and plot that with data fit to new pricing
            a2.clear()
            # Check which indicator will be plotted
            if bottom_indicator[0] == 'macd':
                # Show MACD Line, Signal and difference between
                # X is for now just integers as the dates will be added manually
                a2.plot(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['macd_line'])
                a2.plot(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['signal_line'])
                a2.fill_between(range(len(pricing_dates[cut:])), history_data.iloc[cut:]['histogram'], 0,
                                interpolate=True, color='grey')
                # Do not show more than 16 dates
                a2.xaxis.set_major_locator(mpl_ticker.MaxNLocator(16))
                # Change x axis to show dates
                tick_labels = a2.get_xticklabels(which='both')
                for pos, label in enumerate(tick_labels):
                    try:
                        # Basing on the number of records determine the date
                        tick_labels[pos] = str(
                            pricing_dates[int(round(pos * (len(pricing_dates) / len(tick_labels)), 0))])[:10]
                    except LookupError:
                        tick_labels[pos] = pricing_dates[-1]
                a2.set_xticklabels(tick_labels)
                # Rotate the labels by 30 degrees
                for label in a2.xaxis.get_ticklabels():
                    label.set_rotation(30)
                # a2.xaxis.set_major_formatter(mpl_dates.DateFormatter("%Y-%m-%d"))
                # Set y axis label for indicator
                a2.set_ylabel("MACD")
            elif bottom_indicator[0] == 'rsi':
                # X is for now just integers as the dates will be added manually
                a2.plot(range(len(pricing_dates[cut:])), history_data[cut:]['RSI'])
                # Do not show more than 16 dates
                a2.xaxis.set_major_locator(mpl_ticker.MaxNLocator(16))
                tick_labels = a2.get_xticklabels(which='both')
                for pos, label in enumerate(tick_labels):
                    try:
                        # Basing on the number of records determine the date
                        tick_labels[pos] = str(
                            pricing_dates[int(round(pos * (len(pricing_dates) / len(tick_labels)), 0))])[:10]
                    except LookupError:
                        tick_labels[pos] = pricing_dates[-1]
                a2.set_xticklabels(tick_labels)
                # Rotate the labels by 30 degrees
                for label in a2.xaxis.get_ticklabels():
                    label.set_rotation(30)
                # a2.xaxis.set_major_formatter(mpl_dates.DateFormatter("%Y-%m-%d"))
                a2.set_ylabel("RSI")
                a2.axhline(80, lw=1, ls='--', color='red')
                a2.axhline(20, lw=1, ls='--', color='green')
            else:
                raise RuntimeError("Indicator not defined")

        elif bottom_indicator[1] != 0:
            print("Chart with bottom indicator initialized")
            history_data = indicators_calculator.create_bottom_indicator(history_data, bottom_indicator)

            # Chart shall be count by the indicator periods due to NaN of used moving averages in them
            # It is taken into account when downloading data, user receives given time span
            # MACD needs even larger cut due to signal line created on the faster and slower MAs
            # Methods used are similar to those in function for both chart and bottom indicator
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
                a2.plot(range(len(pricing_dates[cut:])), history_data[cut:]['RSI'])
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
                a2.set_ylabel("RSI")
                a2.axhline(80, lw=1, ls='--', color='red')
                a2.axhline(20, lw=1, ls='--', color='green')
            else:
                raise RuntimeError("Indicator not defined")

        elif chart_indicator[1] != 0:
            # Methods used are similar to those in function for both chart and bottom indicator
            print("Chart with MA initialized")
            chart_indicator_data = indicators_calculator.create_chart_indicator(history_data, chart_indicator)
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
            # Methods used are similar to those in function for both chart and bottom indicator
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
            # Chart shars x axis with main chart
            a1v = a1.twinx()
            # Fill the space between x axis (0) and volume (3rd parameter) with light blue
            # It takes into account cutting excessive data required by the indicators
            a1v.fill_between(range(len(pricing_dates[cut:])), 0,
                             [int(x) for x in history_data.iloc[cut:]['volume']], color="#0000FF", alpha=0.5)
            # Using scale that is 3 times larger that max value in volume allows to put volume in the lower 1/4 part
            # of the main chart
            a1v.set_ylim(0, max(history_data.iloc[cut:]['volume']*3))
            # Grid would overlay on the current one from main chart
            a1v.grid(False)
            a1v.set_ylabel("Volume")


class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        # Create window, set title and icon from the folder with resources
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_iconbitmap(self, bitmap="Additional\chart.ico")
        tk.Tk.wm_title(self, "Trading Station")

        # Create the Frame
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

        # Time frame menu
        change_tf = tk.Menu(menubar, tearoff=1)
        change_tf.add_command(label="H1", command=lambda: tf_changer('H1'))
        change_tf.add_command(label="H4", command=lambda: tf_changer('H4'))
        change_tf.add_command(label="D1", command=lambda: tf_changer('D'))
        change_tf.add_command(label="W1", command=lambda: tf_changer('W'))
        menubar.add_cascade(label="Time frame", menu=change_tf)

        # Period to be shown menu
        window_capacity = tk.Menu(menubar, tearoff=1)
        window_capacity.add_command(label="One Week", command=lambda: window_capacity_changer(7 * 24))
        window_capacity.add_command(label="One Month", command=lambda: window_capacity_changer(31 * 24))
        window_capacity.add_command(label="Half a year", command=lambda: window_capacity_changer(365 / 2 * 24))
        window_capacity.add_command(label="One year", command=lambda: window_capacity_changer(365 * 24))
        window_capacity.add_command(label="Five years", command=lambda: window_capacity_changer(5 * 365 * 24))
        menubar.add_cascade(label="Capacity", menu=window_capacity)

        # Pair to be plotted menu
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

        # Indicator menu
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

        # Turn on/off live data menu
        start_stop = tk.Menu(menubar, tearoff=1)
        start_stop.add_command(label="Start", command=lambda: animation_changer(status='on'))
        start_stop.add_command(label="Stop", command=lambda: animation_changer(status='off'))
        menubar.add_cascade(label="Auto-update", menu=start_stop)

        # Set the prepared menubar object as menu
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
        tk.Frame.__init__(self, parent, bg='#3E3938')
        label = tk.Label(self, text="Home Page", font=LARGE_FONT, bg='white', width=150)
        label.pack(pady=10, anchor='n', fill='x')
        # label.grid(row=0, column=0, columnspan=1, sticky='N', padx=2, pady=2)
        # Using lambda function to prevent from immediate initialization
        button1 = ttk.Button(self, text="Static chart", command=lambda: controller.show_frame(PageOne))
        # button1.grid()
        button1.pack(side='left', fill='x', expand=True, anchor='n')
        button2 = ttk.Button(self, text="Dynamic chart", command=lambda: (controller.show_frame(PageTwo),
                                                                          chart_status(True)))
        # button2.grid()
        button2.pack(side='left', fill='x', expand=True, anchor='n')
        # button3 = ttk.Button(self, text='Test', command=lambda: controller.show_frame(PageOne))
        # button3.grid()
        # button3.pack(side='left', fill='x', expand=True, anchor='n')
        button4 = ttk.Button(self, text="Open website component",
                             # command=lambda: webbrowser.open_new("http://34.229.182.65"))
                             command=lambda: webbrowser.open_new("http://127.0.0.1:4454"))
        button4.pack(side='left', fill='x', expand=True, anchor='n')


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg='#3E3938')
        # fake_label = tk.Label(self, text='', width=194, bg='#3E3938', anchor='e', height=1)
        # fake_label.grid(row=0, column=0, columnspan=194)
        # fake_label_2 = tk.Label(self, text='', width=1, height=44, anchor='s', bg='#3E3938')
        # fake_label_2.grid(row=1, column=0, rowspan=44)
        label = tk.Label(self, text="Static chart page", font=LARGE_FONT, width=20, bg='#3E3938', fg='white')
        # label.grid(row=1, column=97)
        label.pack(padx=10, pady=10)
        # Using lambda function to prevent from immediate initialization
        button1 = ttk.Button(self, text="Return to Home Page", width=20,
                             command=lambda: controller.show_frame(StartPage))
        # button1.grid(row=2, column=97)
        button1.pack()
        # load data that are about to be plotted (only first time the chart is shown) later only the last candle
        # is updated with usage of animate function
        self.create_chart()
        # self.create_table()

    def create_table(self):
        label_1 = tk.Label(self, text='testing', width=8, bg='white', anchor='center', height=1)
        label_2 = tk.Label(self, text='testing', width=8, bg='white', anchor='center', height=1)
        label_3 = tk.Label(self, text='testing', width=8, bg='white', anchor='center', height=1)
        label_4 = tk.Label(self, text='testing', width=8, bg='white', anchor='center', height=1)
        label_5 = tk.Label(self, text='testing', width=8, bg='white', anchor='center', height=1)
        label_6 = tk.Label(self, text='testing', width=8, bg='white', anchor='center', height=1)
        canvas_fill = tk.Canvas(self, bg='white', height=10, width=10)
        canvas_fill.create_polygon(10,10,10,10)
        fake_label = tk.Label(self, bg='white', width=18)
        label_1.grid(row=5, column=10, columnspan=8)
        label_2.grid(row=5, column=19, columnspan=8)
        label_3.grid(row=5, column=28, columnspan=8)
        fake_label.grid(row=6, column=10, columnspan=24)
        label_4.grid(row=7, column=10, columnspan=8)
        label_5.grid(row=7, column=19, columnspan=8)
        label_6.grid(row=7, column=28, columnspan=8)
        canvas_fill.grid(row=4, column=9, columnspan=30, rowspan=10)

    def create_chart(self, load_from='api', user_pair_choice=0):
        # data_handler is responsible to load data from API and SQL database
        if load_from == 'api':
            api_connector = RequestInstrument()
            self.history_data = api_connector.perform_request(pair_choice=user_pair_choice,
                                                              candles_count=150, set_granularity='H1')
        elif load_from == 'db':
            data_handler = DataHandler()
            self.history_data = data_handler.create_df()
        else:
            raise ValueError("Invalid command!")

        # Place the chart
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
        button1 = ttk.Button(self, text='Return to Home Page', command=lambda: (controller.show_frame(StartPage),
                                                                                chart_status(False)))
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
# Activate animation only if chart page is open
ani = animation.FuncAnimation(f, animate, interval=2500)
app.mainloop()
