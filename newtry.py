import os
import shutil
from flask import Flask, render_template, request, send_file, make_response
import pandas as pd
import numpy as np
import logging
import warnings


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
if not os.path.exists('logs'):
    os.mkdir('logs')
handler = logging.FileHandler('logs/logs.log')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s- %(filename)s::%(lineno)d - %(funcName)s - %(message)s', datefmt='%d-%b-%y %H:%M %p')
handler.setFormatter(formatter)
logger.addHandler(handler)

warnings.filterwarnings("ignore")


def process_data(input_data_path):
    """
    Process the input data from an Excel file 
    and calculate revenue of employee.

    Args:
        input_data_path (str): The path to the input Excel file.

    Returns:
        pd.DataFrame(grouped_df): A DataFrame containing processed data.

    Raises:
        pd.errors.EmptyDataError: If the input Excel file is empty.
        pd.errors.ParserError: 
        If the input Excel file contains invalid content.
        Exception: If an unexpected error occurs during processing.
    """

    try:
        #       Define the input data list
        input_data = []

        data = pd.read_excel(input_data_path, sheet_name='Sheet1')
        logger.info("File reading done (Sheet1)")

#       Iterate through rows in the DataFrame and append to input_data
        for index, row in data.iterrows():
            project_data = {
                "Proj_start": row["Proj_start"],
                "Proj_end": row["Proj_end"],
            }
            input_data.append(project_data)
#       Initialize a dictionary to store the days worked in each month
        months = [
            "January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"
        ]
        days_worked = {month: [] for month in months}

#       Add column names
        # column_names = months

#       Loop through the input data and calculate days worked for each month
        for entry in input_data:
            start_date = entry["Proj_start"]
            end_date = entry["Proj_end"]

#           Initialize a list to store days worked for this entry
            entry_days_worked = [0] * len(months)

#           Calculate days worked for each month
            while start_date <= end_date:
                entry_days_worked[start_date.month - 1] += 1
                start_date += pd.DateOffset(days=1)

#           Append the entry's days worked to the respective month
            for i, month in enumerate(months):
                days_worked[month].append(entry_days_worked[i])

#       Create a DataFrame
        df = pd.DataFrame(days_worked)

        Month_df = df[[
            'January', 'February', 'March', 'April', 'May', 'June', 'July',
            'August', 'September', 'October', 'November', 'December'
        ]] / [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        Month_df = np.ceil(Month_df * 100) / 100
        Month_df.insert(0, 'Emp_ID', data['Emp_ID'])
        Month_df.insert(1, 'Project', data['Project'])
        x = (data['Proj_end'] - data['Proj_start']).dt.days
        data["proj_Timeline"] = x / 30

#       Create boolean masks for Rate_per_day, Rate_per_month, and Rate_PO
        mask_day = data['Rate_per_day'] > 0
        mask_month = data['Rate_per_month'] > 0
        mask_po = data['Rate_PO'] > 0

#       Use np.where to conditionally calculate Monthly_revenue
        data['Monthly_revenue'] = pd.Series(
            np.where(
                mask_day, data['Rate_per_day'] * 21,
                np.where(
                    mask_month, data['Rate_per_month'],
                    np.where(mask_po, data['Rate_PO'] / data['proj_Timeline'],
                             0))))

        b = data[[
            "Emp_ID", "Name", "Month_sal", "Project", "PO_No",
            "Monthly_revenue", "Proj_start", "Proj_end"
        ]]

        result = pd.merge(Month_df, b, on=['Emp_ID', 'Project'])
        result = result.iloc[:, [
            0, 14, 15, 1, 16, 17, 18, 19, 2, 3, 4,
            5, 6, 7, 8, 9, 10, 11, 12, 13
        ]]

        result[[
            'January', 'February', 'March', 'April', 'May', 'June', 'July',
            'August', 'September', 'October', 'November', 'December'
        ]] = result[[
            'January', 'February', 'March', 'April', 'May', 'June', 'July',
            'August', 'September', 'October', 'November', 'December'
        ]].multiply(result['Monthly_revenue'], axis=0)

#       Group data by month and aggregate project-related information into list
        grouped_df = result.groupby(['Emp_ID']).agg({
            'Name': 'unique',
            'Project': 'unique',
            'PO_No': 'unique',
            'Month_sal': 'unique',
            'Monthly_revenue': 'sum',
            'Proj_start': 'unique',
            'Proj_end': 'unique',
            'January': 'sum',
            'February': 'sum',
            'March': 'sum',
            'April': 'sum',
            'May': 'sum',
            'June': 'sum',
            'July': 'sum',
            'August': 'sum',
            'September': 'sum',
            'October': 'sum',
            'November': 'sum',
            'December': 'sum'
        })

        grouped_df = grouped_df.reset_index()
#       Return the processed data or any relevant results
        return grouped_df
    except pd.errors.EmptyDataError:
        error_message = "Error: The input Excel file is empty."
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response("Error: The input Excel file is empty.", 400)
        return response

    except pd.errors.ParserError:
        error_message = "Error: The input Excel file contains invalid content, Please select valid input file"
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response(
            "Error: The input Excel file contains invalid content, Please select valid input file", 400)
        return response
    except Exception:
        error_message = "Error: The input Excel file contains invalid content, Please select valid input file"
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response(
            "Error: The input Excel file contains invalid content, Please select valid input file", 400)
        return response


# 2nd function used for fetch revenue of selected month and their profit_loss
def get_employee_data_by_months(grouped_df, selected_months, input_data_path):
    """
    Extract employee data by specified months and calculate revenue with 
    Profit_Loss.

    Args:
        grouped_df (pd.DataFrame): 
        DataFrame containing grouped and processed data.
        selected_months (list): 
        List of selected months for data extraction,Profit_Loss Calculations.
        input_data_path (str): The path to the input Excel file.

    Returns:
        pd.DataFrame:DataFrames containing employee revenue with Profit_Loss by 
        selected months and overall profit/loss data.
    """

    while True:
        months = selected_months

#       Check if all specified month columns exist in the DataFrame
        if all(month in grouped_df.columns for month in months):
            break           # Break the loop if all months are valid
        else:
            invalid_months = [
                month for month in months if month not in grouped_df.columns]
            logger.error(
                f"The following columns do not exist in the DataFrame: {', '.join(invalid_months)}. Please try again.")
            break

#   Initialize an empty list to store DataFrames for each month
    dataframes = []
    try:
        for i in months:
            columns_to_fetch = ['Emp_ID', 'Name', 'Month_sal',
                                'Project', 'PO_No', 'Proj_start', 'Proj_end'] + [i]
            employee_data_month = grouped_df[columns_to_fetch]

            employee_data_month[f"P_L_{i}"] = employee_data_month[i] - \
                employee_data_month['Month_sal']
            employee_data_month[f"P_L_{i}_%"] = employee_data_month.apply(lambda row:
                                                                          ((row[i] - row['Month_sal']) / row[i] * 100)
                                                                          if row[i] > 0 else 0, axis=1)

            employee_data_month = employee_data_month.round(2)

#           Check if the DataFrame is empty or has no valid data
            if employee_data_month.empty or not any(
                    employee_data_month[column].notna().any() for column in employee_data_month.columns):
                print(f"DataFrame for {i} is empty or has no valid data.")
                continue        # Skip empty DataFrames

#           Append the DataFrame for this month to the list
            dataframes.append(employee_data_month)

#       Concatenate all DataFrames into a single DataFrame, removing duplicate columns
        result_df = pd.concat(dataframes, axis=1).loc[:, ~pd.concat(
            dataframes, axis=1).columns.duplicated()]
    except Exception as e:
        error_message = "Column in input Excel file (Sheet1) is not valid, Please check column name as standard"
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response(
            "Column in input Excel file (Sheet1) is not valid, Please check column name as standard", 400)
        return response

    for col in result_df.columns:
        #       Use str.replace to remove square brackets for string values
        result_df[col] = result_df[col].apply(lambda x: str(
            x).replace('[', '').replace(']', '').replace("'", ""))

    for col in result_df.columns[0:5]:
        try:
            result_df[col] = pd.to_numeric(
                result_df[col], errors='coerce').astype(int)
        except ValueError:
            pass

    for col in result_df.columns[7:]:
        try:
            result_df[col] = pd.to_numeric(
                result_df[col], errors='coerce').astype(float).round(2)
        except ValueError:
            pass

    result_df['PO_No'] = result_df['PO_No'].replace('nan', 'NA')
    result_df[['Proj_start', 'Proj_end']] = result_df[[
        'Proj_start', 'Proj_end']].replace('NaT', 'NA')
    result_df['Proj_start'] = result_df['Proj_start'].apply(
        lambda input_string: ', '.join(date.split('T')[0] for date in input_string.split()))
    result_df['Proj_end'] = result_df['Proj_end'].apply(
        lambda input_string: ', '.join(date.split('T')[0] for date in input_string.split()))

#   2nd Requirement - Overall Profit Loss
    sheet2 = pd.read_excel(input_data_path, sheet_name='Sheet2')
    logger.info("File reading done (Sheet2)")
    a = result_df['Month_sal'].sum()
    sheet2['Month_sal'] = a
    sheet2['Total_Expenses'] = sheet2.iloc[:, 0:8].sum(axis=1)

    months1 = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
               'August', 'September', 'October', 'November', 'December']

    filtered_columns = [col for col in result_df.columns if col in months1]

#   Create a new DataFrame with only the desired columns
    new_df = result_df[filtered_columns]
    new_df = new_df.sum()
    a = pd.DataFrame(new_df).T
    final_df = pd.concat([sheet2, a], axis=1)

    dataframe = []
    try:
        for i in a.columns:
            #           Include Rent, Professional Fees, Other Operating Cost, Stipend Expenses, Asstes(Laptop, Headphone etc), Annual Meet Expense, Taxes(Advance & SA Tax), Month_sal, Total_Expenses and the specified month columns
            columns_fetch = ['Rent', 'Professional Fees', 'Other Operating Cost', 'Stipend Expenses',
                             'Asstes (Laptop, Headphone etc)', 'Annual Meet Expense', 'Taxes (Advance & SA Tax)', 'Month_sal', 'Total_Expenses'] + [i]
            overall = final_df[columns_fetch]

            overall[f"P_L_{i}"] = (overall[i] - overall['Total_Expenses'])

            dataframe.append(overall)

#           Concatenate all DataFrames into a single DataFrame, removing duplicate columns
            result_df1 = pd.concat(dataframe, axis=1).loc[:, ~pd.concat(
                dataframe, axis=1).columns.duplicated()]
            result_df1.T.reset_index()

        return result_df, result_df1
    except Exception as e:
        error_message = "Column in input Excel file (Sheet2) is not valid, Please check column name as standard"
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response(
            "Column in input Excel file (Sheet2) is not valid, Please check column name as standard.", 404)
        return response


# UI Part
app = Flask(
    __name__, static_folder=r"C:\Users\Admin\OneDrive - bizmetric.com\Desktop\final\templates")


@app.route('/')
def index():
    logger.info("Accessed the index route")
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    logger.info("Received POST request to process data")
    if 'file' not in request.files:
        error_message = "No file Selected"
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response("No file selected. Please select a file", 404)
        return response

    file = request.files['file']

#   Check if the file has a filename
    if file.filename == '':
        error_message = "No Selected Files"
        logger.error(error_message)
        # return render_template('error.html', error_message=error_message)
        response = make_response("No file selected. Please select a file", 404)
        return response

#   Specify the path to the "flask_uploads" folder on your desktop
    temp_dir = os.path.join(os.path.expanduser('~'),
                            'Desktop', 'flask_uploads')

    # try:
    #Ensure the temporary directory exists, or create it
    os.makedirs(temp_dir, exist_ok=True)
    logger.info("Create temporary directory")

#       Save the uploaded file to the temporary directory
    file_path = os.path.join(temp_dir, 'temp_file.xlsx')
    file.save(file_path)

        # try:

    #Process the uploaded file using the process_data function
    grouped_df = process_data(file_path)
    logger.info("Calling function : process_data")
#           Get the selected months from the form
    selected_months = request.form.get(
        "months").replace(" ", "").split(",")
    logger.info(f"Months Selected :{selected_months}")


#           Call the get_employee_data_by_months function with selected months as input
    r1, r2 = get_employee_data_by_months(
        grouped_df, selected_months, file_path)
    logger.info("Calling function : get_employee_data_by_months")

    # transpose
    r2 = r2.T.reset_index()

#           Define the result file path
    result_file_path = os.path.join(temp_dir, 'revenue.xlsx')

#           Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(result_file_path, engine='xlsxwriter')

#           Convert the DataFrame to an XlsxWriter Excel object
    r1.to_excel(writer, index=False, sheet_name='Monthly_MIS')
    r2.to_excel(writer, startcol=0, index=False,
                header=False, sheet_name='Operating_Cost')
                

#           Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Monthly_MIS']
    worksheet2 = writer.sheets['Operating_Cost']

    # Merge two cells and set the merged cell's value
    # worksheet2.merge_range('A1:B1', 'Operating Cost', workbook.add_format({'align': 'center', 'valign': 'vcenter'}))
    # worksheet2.add_format

#           Define formats for cell coloring
    navy_blue_format = workbook.add_format(
        {'bg_color': '#0070C0', 'border': 1})
    green_format = workbook.add_format(
        {'bg_color': '#09991E', 'border': 1})
    purple_format = workbook.add_format(
        {'bg_color': '#8064A2', 'border': 1})
    orange_format = workbook.add_format(
        {'bg_color': '#FF9900', 'border': 1})
    pink_format = workbook.add_format(
        {'bg_color': '#FF8080', 'border': 1})
    light_blue_format = workbook.add_format(
        {'bg_color': '#DCE6F1', 'border': 1})
    light_green_format = workbook.add_format(
        {'bg_color': '#C4D79B', 'border': 1})
    light_purple_format = workbook.add_format(
        {'bg_color': '#E4DFEC', 'border': 1})
    light_orange_format = workbook.add_format(
        {'bg_color': '#FFFF99', 'border': 1})
    light_pink_format = workbook.add_format(
        {'bg_color': '#FFFFCC', 'border': 1})
    # red_format = workbook.add_format(
    #     {'bg_color': '#FF4D28', 'border': 1})

    # -ve values
    ng_green = workbook.add_format(
        {'bg_color': '#97B953', 'border': 1})
    ng_purple = workbook.add_format(
        {'bg_color': '#B1A0C7', 'border': 1})
    ng_orange = workbook.add_format(
        {'bg_color': '#FFCC66', 'border': 1})
    ng_pink = workbook.add_format({'bg_color': '#FCD5B4', 'border': 1})

#           Determine the number of rows and columns in the DataFrame
    num_rows, num_cols = r1.shape

    for col_num in range(num_cols):
        if col_num < 7:
            cell_value = r1.columns[col_num]
            format_to_apply = navy_blue_format
        elif col_num in [7, 8, 9, 19, 20, 21, 31, 32, 33]:
            cell_value = r1.columns[col_num]
            format_to_apply = green_format
        elif col_num in [10, 11, 12, 22, 23, 24, 34, 35, 36]:
            cell_value = r1.columns[col_num]
            format_to_apply = purple_format
        elif col_num in [13, 14, 15, 25, 26, 27, 37, 38, 39]:
            cell_value = r1.columns[col_num]
            format_to_apply = orange_format
        elif col_num in [16, 17, 18, 28, 29, 30, 40, 41, 42]:
            cell_value = r1.columns[col_num]
            format_to_apply = pink_format
        worksheet.write(0, col_num, cell_value, format_to_apply)

#           Apply formatting to the cells based on your criteria
    for col_num in range(num_cols):
        # Start from row 1 to skip the header
        for row_num in range(1, num_rows + 1):
            numeric_value = pd.to_numeric(cell_value, errors='coerce')
            cell_value = r1.iloc[row_num - 1, col_num]

            if col_num < 7:  # First 6 columns in light grey
                format_to_apply = light_blue_format
            elif col_num in [7, 8, 9, 19, 20, 21, 31, 32, 33]:
                if pd.notna(cell_value) and pd.to_numeric(cell_value, errors='coerce') < 0:
                    format_to_apply = ng_green
                else:
                    format_to_apply = light_green_format
            elif col_num in [10, 11, 12, 22, 23, 24, 34, 35, 36]:
                if pd.notna(cell_value) and pd.to_numeric(cell_value, errors='coerce') < 0:
                    format_to_apply = ng_purple
                else:
                    format_to_apply = light_purple_format
            elif col_num in [13, 14, 15, 25, 26, 27, 37, 38, 39]:
                if pd.notna(cell_value) and pd.to_numeric(cell_value, errors='coerce') < 0:
                    format_to_apply = ng_orange
                else:
                    format_to_apply = light_orange_format
            elif col_num in [16, 17, 18, 28, 29, 30, 40, 41, 42]:
                if pd.notna(cell_value) and pd.to_numeric(cell_value, errors='coerce') < 0:
                    format_to_apply = ng_pink
                else:
                    format_to_apply = light_pink_format
            else:
                format_to_apply = None

            # if pd.notna(cell_value):
            #     numeric_value = pd.to_numeric(cell_value, errors='coerce')
            #     if not pd.isna(numeric_value) and numeric_value < 0:
            #         format_to_apply = red_format
            if format_to_apply:
                #                       Apply both color and borders
                worksheet.write(row_num, col_num,
                                cell_value, format_to_apply)

    # colour code for sheet2
    # worksheet2 = writer.sheets['Operating_Cost']
    # Merge two cells and set the merged cell's value
    cell_format = workbook.add_format(
        {'bg_color': '#3366FF', 'align': 'center', 'valign': 'vcenter', 'border': 1})
    worksheet2.merge_range('A1:B1', 'Operating Cost', cell_format)
    # worksheet2.merge_range('A1:B1', 'Operating Cost', workbook.add_format({'align': 'center', 'valign': 'vcenter'}))

    # Determine the number of rows and columns in the DataFrame
    num_rows2, num_cols2 = r2.shape
    # Apply formatting to the cells based on your criteria
    for col_num in range(num_cols2):
        # Start from row 1 to skip the header
        for row_num in range(1, num_rows2 + 1):
            cell_value2 = r2.iloc[row_num - 1, col_num]
            if col_num == 0:
                if row_num <= 9:
                    format_to_apply = light_blue_format
                elif row_num in [10, 11, 18, 19, 26, 27]:
                    format_to_apply = light_green_format
                elif row_num in [12, 13, 20, 21, 28, 29]:
                    format_to_apply = light_purple_format
                elif row_num in [14, 15, 22, 23, 30, 31]:
                    format_to_apply = light_orange_format
                elif row_num in [16, 17, 24, 25, 32, 33]:
                    format_to_apply = light_pink_format
            elif col_num == 1:
                if row_num <= 9:
                    format_to_apply = light_blue_format
                # elif row_num == 9:
                #     format_to_apply = navy_blue_format
                elif row_num in [10, 11, 18, 19, 26, 27]:
                    format_to_apply = light_green_format
                elif row_num in [12, 13, 20, 21, 28, 29]:
                    format_to_apply = light_purple_format
                elif row_num in [14, 15, 22, 23, 30, 31]:
                    format_to_apply = light_orange_format
                elif row_num in [16, 17, 24, 25, 32, 33]:
                    format_to_apply = light_pink_format
            else:
                format_to_apply = None
            if format_to_apply:
                # Apply both color and borders
                worksheet2.write(row_num, col_num,
                                    cell_value2, format_to_apply)


#           Save the Excel file
    writer.save()
    writer.close()
    logger.info("Saved and Closed Excel file")

#           Send the processed data file as a response
    return send_file(result_file_path, as_attachment=True)
    # except pd.errors.ParserError:
    error_message = "Error: The uploaded file is not a valid Excel file."
    # return render_template('error.html', error_message=error_message)
    response = make_response(
        "Error: The uploaded file is not a valid Excel file.", 404)
    return response
    # except Exception:
    error_message = "Make sure you have provided a vaild input FILE and selected the MONTHS"
#           Render the error template with the error message
    # return render_template('error.html', error_message=error_message)
    response = make_response(
        "Make sure you have provided a vaild input FILE and selected the MONTHS", 404)
    return response
# finally:
    #       Clean up: Remove the temporary directory and its contents
shutil.rmtree('temp_dir', ignore_errors=True)
logger.info("Removed temporary directory")


if __name__ == '__main__':
    logging.info("Starting flask API")
    app.run(debug=True)
    logging.info("Stopped flask API")
