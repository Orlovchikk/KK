from datetime import date


def translate_month_in_str(date_unformatted: date):
    months_translation = {
            'January': 'января',
            'February': 'февраля',
            'March': 'марта',
            'April': 'апреля',
            'May': 'мая',
            'June': 'июня',
            'July': 'июля',
            'August': 'августа',
            'September': 'сентября',
            'October': 'октября',
            'November': 'ноября',
            'December': 'декабря',
        }
    
    date_str = date_unformatted.strftime("%d %B %Y")
    for en, ru in months_translation.items():
        date_str = date_str.replace(en, ru)
        
    return date_str