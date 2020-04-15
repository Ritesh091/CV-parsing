from datetime import datetime

RESUME_SECTIONS_GRAD = [
                    'accomplishments',
                    'experience',
                    'education',
                    'interests',
                    'project',
                    'projects',
                    'project profile'
                    'professional experience',
                    'publications',
                    'skills',
                    'certifications',
                    'objective',
                    'career objective',
                    'summary',
                    'leadership',
                    'hobbies',
                    'declaration'
                ]

def extract_entity_sections_grad(text):
    '''
    Helper function to extract all the raw text from sections of resume specifically for 
    graduates and undergraduates

    :param text: Raw text of resume
    :return: dictionary of entities
    '''
    text_split = [i.strip() for i in text.split(' ')]
    # sections_in_resume = [i for i in text_split if i.lower() in sections]
    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(RESUME_SECTIONS_GRAD)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in RESUME_SECTIONS_GRAD:
            if p_key in entities.keys():
                key = p_key
            else:
                entities[p_key] = []
                key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)

    return entities

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def get_number_of_months_from_dates(date1, date2):
    '''
    Helper function to extract total months of experience from a resume

    :param date1: Starting date
    :param date2: Ending date
    :return: months of experience from date1 to date2
    '''
    if date2.lower() == 'present':
        date2 = datetime.now().strftime('%b %Y')   
    try:
        if (hasNumbers(date1[3:]) == True) and (len(date1[3:].strip()) == 2): 
            date1 = date1[:3] + ' ' + '20'+date1[3:].strip()
    except IndexError:
        return     
    try:
        if len(date1.split()[0]) > 3:
            date1 = date1.split()
            date1 = date1[0][:3] + ' ' + date1[1]
        if len(date2.split()[0]) > 3:
            date2 = date2.split()
            date2 = date2[0][:3] + ' ' + date2[1]
    except IndexError:
        return 0
    
    try: 
        date1 = datetime.strptime(str(date1), '%b %Y')
        date2 = datetime.strptime(str(date2), '%b %Y')
        months_of_experience = relativedelta.relativedelta(date2, date1)
        months_of_experience = months_of_experience.years * 12 + months_of_experience.months
    except ValueError:
        return 0
    return months_of_experience

def get_total_experience(experience_list):
    '''
    Wrapper function to extract total months of experience from a resume

    :param experience_list: list of experience text extracted
    :return: total months of experience
    '''
    exp_ = []
#     for line in experience_list:
    experience = re.search('(?P<fmonth>\w+.\d+)\s*(\D|to)\s*(?P<smonth>\w+.\d+|present)', experience_list, re.I)
    if experience:
        exp_.append(experience.groups())
    print(exp_)
    total_experience_in_months = sum([get_number_of_months_from_dates(i[0], i[2]) for i in exp_])
    return total_experience_in_months




