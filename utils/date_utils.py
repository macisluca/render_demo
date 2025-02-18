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
