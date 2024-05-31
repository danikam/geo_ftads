#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 28 15:42:00 2024

@author: danikam
"""

# Import needed modules
import sys

import numpy as np
import pandas as pd
import geopandas as gpd
from CommonTools import get_top_dir
import matplotlib.pyplot as plt
import glob
import re

zone_mapping = {
    'north': 'NORTH',
    'far_west': 'FWEST',
    'west': 'WEST',
    'north_central': 'NCENT',
    'east': 'EAST',
    'south_central': 'SCENT',
    'south': 'SOUTH',
    'coast': 'COAST'
}

month_names = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

def read_load_data(paths):
    load_data = pd.DataFrame()
    for path in paths:
        data = pd.read_excel(path)
        load_data = pd.concat([load_data, data], ignore_index=True)
    
    # Remove any 'Hour Ending' rows where time shifts to DST
    load_data = load_data[~load_data['Hour Ending'].str.contains('DST')]
    
    # Adjust 'Hour Ending' for '24:00'
    load_data['Hour Ending'] = load_data['Hour Ending'].apply(correct_datetime)

    # Convert 'Hour Ending' to datetime
    load_data['Hour Ending'] = pd.to_datetime(load_data['Hour Ending'], format="%m/%d/%Y %H:%M")
    
    return load_data
    
def correct_datetime(time_str):
    # Check if time is '24:00' and adjust to '00:00' of the next day
    if time_str.endswith("24:00"):
        # Parse the date part and increment the day
        new_time_str = pd.to_datetime(time_str[:-5]).date() + pd.Timedelta(days=1)
        return new_time_str.strftime("%m/%d/%Y") + " 00:00"
    return time_str
    
def plot_daily_power(load_data):

    # Extract the date for filtering
    load_data['Date'] = load_data['Hour Ending'].dt.date
    
    # Get unique dates that are the first of the month
    first_days = load_data[load_data['Hour Ending'].dt.day == 1]['Date'].unique()
    
    # Filter data for each first of the month
    for date in first_days:
        # Filter data for the specific day
        daily_data = load_data[load_data['Date'] == date]
        
        # Creating a figure and axis objects
        fig, axs = plt.subplots(nrows=8, ncols=1, figsize=(10, 20), sharex=True)
        
        # Title for the whole figure
        fig.suptitle(f'Power Variation for {date}', fontsize=16)
        
        regions = ['COAST', 'EAST', 'FWEST', 'NORTH', 'NCENT', 'SOUTH', 'SCENT', 'WEST']
        
        for i, region in enumerate(regions):
            axs[i].plot(daily_data['Hour Ending'].dt.hour, daily_data[region], label=region)
            axs[i].set_title(region)
            axs[i].set_ylabel('Power (MW)')
        
        # Setting x-label for the last subplot
        axs[-1].set_xlabel('Hour')
        
        # Adjust layout to prevent overlap
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Show the plot
        plt.savefig(f'{top_dir}/plots/daily_power_variation_{date}.png')
        plt.close()
        
def make_daily_ev_demands_fig(top_dir, filename, zone):
    daily_ev_demands = pd.read_csv(filename)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlabel('Hours', fontsize=20)
    ax.set_xlabel('Power (MW)', fontsize=20)
    zone_title = zone.title().replace('_', ' ')
    ax.set_title(f'Power Demands in {zone_title} Zone', fontsize=24)
    ax.tick_params(axis='both', which='major', labelsize=18)
    
    # For each zone, plot the daily variation for each center (and total over all centers)
    colors=['red', 'purple', 'orange', 'teal', 'cyan', 'magenta', 'teal']
    i_center = 0
    for center in daily_ev_demands.columns:
        if center == 'Hours':
            continue
        elif '(MW)' in center:
            center_label = center.replace(' (MW)', '')
            color='black'
            linewidth=3
        else:
            color=colors[i_center]
            linewidth=2
            center_label = center
        
        ax.plot(daily_ev_demands['Hours'], daily_ev_demands[center], label=f'EV Demand ({center_label})', color=color, linewidth=linewidth, zorder=20)
        i_center+=1
        
    return fig, ax
                    
def plot_with_historical_daily_load(top_dir, load_data_df):
    path = f'{top_dir}/data/daily_ev_load_*.csv'
    pattern = re.compile(r'daily_ev_load_([^\.]+).csv')
    for filename in glob.glob(f'{top_dir}/data/daily_ev_load_*.csv'):
        match = pattern.search(filename)
        if match:
            zone = match.group(1)
        
        fig, ax = make_daily_ev_demands_fig(top_dir, filename, zone)

        # Extract the date for filtering
        load_data_df['Date'] = load_data_df['Hour Ending'].dt.date

        # Get unique dates that are the first of the month
        first_days = load_data_df[(load_data_df['Hour Ending'].dt.day == 1) & (load_data_df['Hour Ending'].dt.year == 2023)]['Date'].unique()
        
        # Filter data for each first of the month
        cmap = plt.get_cmap('winter')
        num_plots = len(first_days)
        colors = [cmap(i/num_plots) for i in range(num_plots)]
        i_month=0
        for date in first_days:
            # Filter data for the specific day
            daily_data = load_data_df[load_data_df['Date'] == date]
            if i_month==0 or i_month==11:
                ax.plot(daily_data['Hour Ending'].dt.hour, daily_data[zone_mapping[zone]], color=colors[i_month], label=f'Historical Load ({month_names[i_month+1]})', zorder=i_month, alpha=0.8)
            else:
                ax.plot(daily_data['Hour Ending'].dt.hour, daily_data[zone_mapping[zone]], color=colors[i_month], alpha=0.8)
            i_month+=1
        
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(ymin, ymax*1.5)
        ax.legend(fontsize=18)
        plt.savefig(f'{top_dir}/plots/daily_ev_load_{zone}.png')

# DMM: Need to modify this to plot with max capacity - average (+.- std) on an hourly basis
def plot_with_excess_capacity(top_dir, load_data_df):
    path = f'{top_dir}/data/daily_ev_load_*.csv'
    pattern = re.compile(r'daily_ev_load_([^\.]+).csv')
    for filename in glob.glob(f'{top_dir}/data/daily_ev_load_*.csv'):
        match = pattern.search(filename)
        if match:
            zone = match.group(1)

        # Extract the date for filtering
        load_data_df['Date'] = pd.to_datetime(load_data_df['Hour Ending'].dt.date)

        # Drop zones we're not interested in
        load_data_zone_df = load_data_df[['Hour Ending', 'Date', zone_mapping[zone]]]

        ##### Get the absolute maximum power demand over the full period (approximation of nameplate capacity) #####
        max_load = load_data_zone_df[zone_mapping[zone]].max()
        
        # Extract the hour and month components
        load_data_zone_df['Hour'] = load_data_zone_df['Hour Ending'].dt.hour
        load_data_zone_df['Month'] = load_data_zone_df['Date'].dt.month
        
        for month in range(1,13):
            # Group by the 'Hour' column
            grouped = load_data_zone_df[load_data_zone_df['Month']==month].groupby('Hour')

            # Aggregate the data to get mean, max, min, and std dev
            aggregated_data_df = grouped[zone_mapping[zone]].agg(['mean', 'max', 'min', 'std'])
        
            # Calculate the mean (+/-std), max and min excess based on the maximum load over the month
            aggregated_data_df['Max Load (MW)'] = load_data_zone_df[load_data_zone_df['Month']==month][zone_mapping[zone]].max()
            aggregated_data_df['Mean Excess (MW)'] = aggregated_data_df['Max Load (MW)'] - aggregated_data_df['mean']
            aggregated_data_df['Mean Excess + std (MW)'] = aggregated_data_df['Max Load (MW)'] - aggregated_data_df['mean'] + aggregated_data_df['std']
            aggregated_data_df['Mean Excess - std (MW)'] = aggregated_data_df['Max Load (MW)'] - aggregated_data_df['mean'] - aggregated_data_df['std']
            aggregated_data_df['Max Excess (MW)'] = aggregated_data_df['Max Load (MW)'] - aggregated_data_df['min']
            aggregated_data_df['Min Excess (MW)'] = aggregated_data_df['Max Load (MW)'] - aggregated_data_df['max']
            
            # Reset the index to make 'Hour' a regular column
            aggregated_data_df.reset_index(inplace=True)
    
            aggregated_data_df = aggregated_data_df.drop(['mean', 'max', 'min', 'std'], axis=1)
            
            # Plot along with the EV demand curves
            fig, ax = make_daily_ev_demands_fig(top_dir, filename, zone)
            
            handles, labels = ax.get_legend_handles_labels()
            
            mean_line, = ax.plot(aggregated_data_df['Mean Excess (MW)'], linewidth=3, color='navy')
            std_patch = ax.fill_between(aggregated_data_df['Hour'], aggregated_data_df['Mean Excess - std (MW)'], aggregated_data_df['Mean Excess + std (MW)'], color='blue', alpha=0.4)
            extrema_patch = ax.fill_between(aggregated_data_df['Hour'], aggregated_data_df['Min Excess (MW)'], aggregated_data_df['Max Excess (MW)'], color='blue', alpha=0.2)
        
            ymin, ymax = ax.get_ylim()
            ax.set_ylim(ymin, ymax*1.5)
            month_label=month_names[month]
            zone_title = zone.title().replace('_', ' ')
            ax.set_title(f'{zone_title}: {month_label}', fontsize=24)
            
            handles = handles + [(mean_line, std_patch), extrema_patch]
            labels = labels + ['Mean Excess + Stdev (MW)', 'Min/Max Excess (MW)']
            
            ax.legend(handles, labels, fontsize=16)
            
            plt.savefig(f'{top_dir}/plots/daily_ev_load_with_excess_{zone}_{month_label}.png')
            plt.close()


def main():

    # Get the path to the top level of the Git repo
    top_dir = get_top_dir()
    
    load_data_paths = [f'{top_dir}/data/Native_Load_2023.xlsx', f'{top_dir}/data/Native_Load_2024.xlsx']
    load_data_df = read_load_data(load_data_paths)
        
    plot_with_historical_daily_load(top_dir, load_data_df)
    
    plot_with_excess_capacity(top_dir, load_data_df)
    
main()
