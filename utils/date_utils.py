from datetime import datetime
import re

def transform_date_to_day_first(date_input):
    """
    Transforms a date input into the format DD/MM/YYYY.
    Accepts either a string in YYYY-MM-DD or a datetime object.
    """
    if isinstance(date_input, str):
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD format."
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        return "Invalid input. Please provide a string or datetime object."
    return date_obj.strftime("%d/%m/%Y")

def add_br_to_description(description):
    """
    Adds HTML line breaks to a description string.
    """
    description_with_slashes = description.replace('/', '<br><br>')
    
    def insert_br_at_space(text, limit):
        pattern = r'(.{' + str(limit) + r'}\S*)\s'
        return re.sub(pattern, r'\1<br> ', text)
    
    return insert_br_at_space(description_with_slashes, 50)


def get_majority_category(df_country, selected_variable):
    """
    Given a country’s forecast DataFrame (filtered by forecast date),
    returns the most frequent simplified category.
    For 'violence index', categories are: Mild, Moderate, Intense, Critical.
    For 'battles fatalities', categories are: 
       - No Fatalities (if outcome == 0)
       - Low Fatalities (if 0 < outcome <= 10)
       - Medium Fatalities (if 10 < outcome <= 50)
       - High Fatalities (if outcome > 50)
    """
    if df_country.empty:
        return None

    if selected_variable.lower().strip() == "violence index":
        def get_level(val):
            if val < 25:
                return "Mild"
            elif val < 50:
                return "Moderate"
            elif val < 75:
                return "Intense"
            else:
                return "Critical"
        df_country = df_country.copy()
        df_country["level"] = df_country["outcome"].apply(get_level)
        mode_series = df_country["level"].mode()
        if not mode_series.empty:
            return mode_series.iloc[0]
        else:
            return None

    elif selected_variable.lower().strip() == "battles fatalities":
        def get_battle_category(val):
            if val == 0:
                return "No Fatalities"
            elif val <= 10:
                return "Low Fatalities"
            elif val <= 50:
                return "Medium Fatalities"
            else:
                return "High Fatalities"
        df_country = df_country.copy()
        df_country["category"] = df_country["outcome"].apply(get_battle_category)
        mode_series = df_country["category"].mode()
        if not mode_series.empty:
            return mode_series.iloc[0]
        else:
            return None
    else:
        # For other variables, you might decide not to create a simplified grouping.
        return None
